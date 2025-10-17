from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.app_admin.mod_siteadmin.models import Site, Organization, Membership, Role


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ["name", "description", "active"]  # slug is auto-generated
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        inst: Site = super().save(commit=False)
        # Auto-generate slug if missing
        if not getattr(inst, 'slug', None):
            base = slugify(inst.name or "") or "site"
            slug = base
            i = 2
            while Site.objects.filter(slug=slug).exclude(pk=inst.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            inst.slug = slug
        if commit:
            inst.save()
        return inst


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "description", "active"]  # slug is auto-generated
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self._site = kwargs.pop("site", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        inst: Organization = super().save(commit=False)
        # Ensure site if passed via form context but not on instance yet
        if self._site is not None and not getattr(inst, 'site_id', None):
            inst.site = self._site
        # Auto-generate slug if missing
        if not getattr(inst, 'slug', None):
            base = slugify(inst.name or "") or "org"
            slug = base
            i = 2
            # Ensure per-site uniqueness
            while Organization.objects.filter(site=inst.site, slug=slug).exclude(pk=inst.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            inst.slug = slug
        if commit:
            inst.save()
        return inst


class MembershipForm(forms.ModelForm):
    class Meta:
        model = Membership
        fields = ["user", "role", "organization", "active"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "organization": forms.Select(attrs={"class": "form-select"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        site = kwargs.pop("site", None)
        role_code = kwargs.pop("role_code", None)
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["user"].queryset = User.objects.order_by("username")
        self.fields["role"].queryset = Role.objects.all().order_by("label")
        if role_code:
            try:
                self.fields["role"].initial = Role.objects.get(code=role_code).id
            except Role.DoesNotExist:
                pass
        if site is not None:
            self.fields["organization"].queryset = Organization.objects.filter(site=site, active=True).order_by("name")
        # Allow empty organization (site-level membership)
        self.fields["organization"].required = False


class BulkOrgAdminForm(forms.Form):
    user = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={"class": "form-select"}))
    active = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def __init__(self, *args, **kwargs):
        site = kwargs.pop("site", None)
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields["user"].queryset = User.objects.order_by("username")
