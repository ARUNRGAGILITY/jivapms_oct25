from django import forms

from .models import OrganizationSection, OrganizationTypeOption


class OrganizationSectionForm(forms.ModelForm):
    class Meta:
        model = OrganizationSection
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 6, "class": "form-control"}),
        }


class OrganizationSectionTypeForm(forms.ModelForm):
    """Specialized form for the Overview → Type section using a dropdown of options with a Custom entry."""
    TYPE_CUSTOM_SENTINEL = "__custom__"
    type_choice = forms.ChoiceField(label="Type", choices=(), required=False)
    other_value = forms.CharField(label="Custom type", required=False)

    class Meta:
        model = OrganizationSection
        fields = ["content"]  # we'll store the selected value into content

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure default options exist if none have been created yet
        if not OrganizationTypeOption.all_objects.exists():
            base = [
                ("Project-based", 10),
                ("Product-based", 20),
                ("Service-based", 30),
                ("Consulting-based", 40),
                ("Custom", 50),
                ("Hybrid Type", 60),
            ]
            for name, pos in base:
                OrganizationTypeOption.all_objects.update_or_create(name=name, defaults={"position": pos, "active": True, "deleted": False})
        opts = OrganizationTypeOption.objects.filter(active=True, deleted=False).order_by("position", "name")
        choices = [(o.name, o.name) for o in opts]
        choices.append((self.TYPE_CUSTOM_SENTINEL, "Custom…"))
        self.fields["type_choice"].choices = choices
        # Preselect from content if present
        if self.instance and self.instance.content:
            # If current content matches an existing option, preselect it; else select Custom and fill other_value
            names = {v for v, _ in choices}
            if self.instance.content in names:
                self.fields["type_choice"].initial = self.instance.content
            else:
                self.fields["type_choice"].initial = self.TYPE_CUSTOM_SENTINEL
                self.fields["other_value"].initial = self.instance.content

    def clean(self):
        cleaned = super().clean()
        sel = cleaned.get("type_choice")
        if sel == self.TYPE_CUSTOM_SENTINEL:
            val = (cleaned.get("other_value") or "").strip()
            cleaned["content"] = val
        else:
            cleaned["content"] = sel or ""
        return cleaned


class OrganizationTypeOptionForm(forms.ModelForm):
    class Meta:
        model = OrganizationTypeOption
        fields = ["name", "position"]