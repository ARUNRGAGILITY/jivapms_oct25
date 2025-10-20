from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from apps.app_admin.mod_siteadmin.models import Site, Organization, Membership, Role
from apps.app_organization.mod_organization.models import OrganizationSection, OrganizationTypeOption
from apps.app_organization.mod_organization.forms import (
    OrganizationSectionForm,
    OrganizationSectionTypeForm,
    OrganizationTypeOptionForm,
)
from .forms import SiteForm, OrganizationForm, MembershipForm, BulkOrgAdminForm


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _is_site_admin(user, site: Site | None = None) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if site is None:
        return False
    role = Role.objects.filter(code='siteadmin').first()
    if not role:
        return False
    return Membership.objects.filter(user=user, site=site, organization__isnull=True, role=role, active=True).exists()


def _is_org_admin(user, site: Site, org: Organization) -> bool:
    role = Role.objects.filter(code='orgadmin').first()
    if not role:
        return False
    return Membership.objects.filter(user=user, site=site, organization=org, role=role, active=True).exists()


@login_required
def dashboard(request):
    # Staff sees all sites; site admins see their sites; others forbidden
    if request.user.is_staff or request.user.is_superuser:
        sites = Site.objects.all().order_by('name')
        deleted_sites_qs = Site.all_objects.dead().filter(blocked=False).order_by('name')
    else:
        role_siteadmin = Role.objects.filter(code='siteadmin').first()
        if not role_siteadmin:
            return HttpResponseForbidden()
        sites = Site.objects.filter(
            memberships__user=request.user,
            memberships__role=role_siteadmin,
            memberships__organization__isnull=True,
            memberships__active=True,
        ).distinct().order_by('name')
        if not sites.exists():
            return HttpResponseForbidden()
        deleted_sites_qs = Site.all_objects.dead().filter(
            memberships__user=request.user,
            memberships__role=role_siteadmin,
            memberships__organization__isnull=True,
            memberships__active=True,
        ).distinct().filter(blocked=False).order_by('name')

    role_siteadmin = Role.objects.filter(code='siteadmin').first()
    data = []
    for s in sites:
        admins_qs = Membership.objects.filter(site=s, organization__isnull=True, role=role_siteadmin, active=True) if role_siteadmin else Membership.objects.none()
        org_count = s.organizations.count()
        member_count = Membership.objects.filter(site=s, active=True).count()
        data.append({
            'site': s,
            'admins': [m.user for m in admins_qs],
            'org_count': org_count,
            'member_count': member_count,
        })

    # Deleted items (recycle bin) - keep minimal info
    deleted_items = []
    for s in deleted_sites_qs:
        deleted_items.append({
            'site': s,
            'org_count': s.organizations.count(),
        })

    view_mode = request.GET.get('view', 'card')
    if view_mode not in {'card', 'table'}:
        view_mode = 'card'

    show_bin = request.GET.get('bin') == '1'
    allowed_sizes = ['10', '20', '30', '40', '50', 'all']
    page_size_raw = request.GET.get('page_size', '10')
    if page_size_raw not in allowed_sizes:
        page_size_raw = '10'
    page_size = None if page_size_raw == 'all' else int(page_size_raw)
    page_number = int(request.GET.get('page', '1') or 1)

    # Build paginated pages
    items_page = None
    deleted_page = None
    if page_size:
        items_page = Paginator(data, page_size).get_page(page_number)
        deleted_page = Paginator(deleted_items, page_size).get_page(page_number)
    else:
        # show all as one page
        class _AllPage:
            def __init__(self, objs):
                self.object_list = objs
                self.paginator = type('P', (), {'count': len(objs)})
                self.number = 1
                self.has_previous = False
                self.has_next = False
        items_page = _AllPage(data)
        deleted_page = _AllPage(deleted_items)

    ctx = {
        'items_page': items_page,
        'deleted_page': deleted_page,
        'deleted_count': len(deleted_items),
        'view_mode': view_mode,
        'show_bin': show_bin,
        'page_size': page_size_raw,
        'page_sizes': allowed_sizes,
    }
    return render(request, 'app_site/siteadmin/dashboard.html', ctx)


@login_required
def site_detail(request, site_id: int):
    s = get_object_or_404(Site.objects.all(), pk=site_id)
    if not _is_site_admin(request.user, s):
        return HttpResponseForbidden()
    role_siteadmin = Role.objects.filter(code='siteadmin').first()
    role_orgadmin = Role.objects.filter(code='orgadmin').first()

    admins_qs = Membership.objects.select_related('user').filter(site=s, organization__isnull=True, role=role_siteadmin, active=True) if role_siteadmin else Membership.objects.none()
    members_qs = Membership.objects.select_related('user', 'organization', 'role').filter(site=s, active=True)
    orgs = Organization.objects.filter(site=s).order_by('name')
    orgs_deleted_qs = Organization.all_objects.dead().filter(site=s).order_by('name')
    org_show_bin = request.GET.get('org_bin') == '1'
    # Determine which tab to show initially (default to overview)
    active_tab = request.GET.get('tab', 'overview').lower()
    if active_tab not in {'overview', 'members', 'organizations'}:
        active_tab = 'overview'

    context = {
        'site': s,
        'admins': [m.user for m in admins_qs],
        'members': members_qs,
        'orgs': orgs,
    'role_siteadmin': role_siteadmin,
        'role_orgadmin': role_orgadmin,
        'active_tab': active_tab,
    'orgs_deleted': orgs_deleted_qs,
    'orgs_deleted_count': orgs_deleted_qs.count(),
    'org_show_bin': org_show_bin,
    }
    return render(request, 'app_site/siteadmin/site_detail.html', context)


# Organization detail view
@login_required
def organization_detail(request, site_id: int, org_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    role_orgadmin = Role.objects.filter(code='orgadmin').first()
    members_qs = Membership.objects.select_related('user', 'role').filter(site=site, organization=org, active=True)
    admins = [m.user for m in members_qs if role_orgadmin and m.role_id == role_orgadmin.id]
    ctx = {
        'site': site,
        'org': org,
        'members': members_qs,
        'admins': admins,
    }
    return render(request, 'app_site/siteadmin/org_detail.html', ctx)


# Organization home with tabs and scrollspy TOC
@login_required
def organization_home(request, site_id: int, org_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    active_tab = request.GET.get('tab', 'overview').lower()
    if active_tab not in {'overview','business','delivery','operations','metrics','review','reports'}:
        active_tab = 'overview'
    # Ensure baseline sections exist for known tabs/titles
    default_titles = {
        'overview': ['Vision','Mission','Value','Strategy','Structure','Type','Summary'],
        'delivery': ['Portfolio','Program','Projects / Products / Services'],
    }
    if active_tab in default_titles:
        for idx, title in enumerate(default_titles[active_tab]):
            key = slugify(title)[:64]
            sec, created = OrganizationSection.objects.get_or_create(
                organization=org, tab=active_tab, key=key, defaults={'title': title, 'order': idx}
            )
            # Do not change order if already exists; only set on creation
    # Load sections and build maps
    sections = OrganizationSection.objects.filter(organization=org, active=True).order_by('tab', 'order', 'id')
    meta: dict[str, dict[str, str]] = {}
    meta_ids: dict[str, dict[str, int]] = {}
    for sec in sections:
        meta.setdefault(sec.tab, {})[sec.title] = sec.content or ''
        meta_ids.setdefault(sec.tab, {})[sec.title] = sec.id
    org.meta = meta
    org.meta_ids = meta_ids
    # Permissions for editing
    is_site_admin = _is_site_admin(request.user, site)
    is_org_admin = _is_org_admin(request.user, site, org)
    # Org admin can edit only a subset of sections; site admin can edit all
    editable_by_org_admin = {
        'overview': {t: True for t in ['Vision','Mission','Value','Strategy','Structure','Type','Summary']},
        'delivery': {t: True for t in ['Portfolio','Program','Projects / Products / Services']},
    }
    ctx = {
        'site': site,
        'org': org,
        'active_tab': active_tab,
        'can_manage_types': (is_site_admin or is_org_admin),
        'is_site_admin': is_site_admin,
        'is_org_admin': is_org_admin,
        'editable_by_org_admin': editable_by_org_admin,
    }
    return render(request, 'app_site/siteadmin/org_home.html', ctx)


# ----- Organization content modals -----
@login_required
@require_http_methods(["GET", "POST"])
def organization_section_edit_modal(request, site_id: int, org_id: int, section_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    is_site_admin = _is_site_admin(request.user, site)
    is_org_admin = _is_org_admin(request.user, site, org)
    if not (is_site_admin or is_org_admin):
        return HttpResponseForbidden()
    sec = get_object_or_404(OrganizationSection.objects.all(), pk=section_id, organization=org)
    # If org admin, restrict to allowed sections
    if is_org_admin and not is_site_admin:
        allowed_titles = {
            'overview': {'Vision','Mission','Value','Strategy','Structure','Type','Summary'},
            'delivery': {'Portfolio','Program','Projects / Products / Services'},
        }
        if sec.title not in allowed_titles.get(sec.tab, set()):
            return HttpResponseForbidden()
    # Choose form: special case for Overview → Type
    if sec.tab == 'overview' and sec.title.lower() == 'type':
        FormClass = OrganizationSectionTypeForm
        template = 'app_site/siteadmin/_org_section_type_form.html'
    else:
        FormClass = OrganizationSectionForm
        template = 'app_site/siteadmin/_org_section_form.html'
    if request.method == 'POST':
        form = FormClass(request.POST, instance=sec)
        if form.is_valid():
            form.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": f"{sec.title} updated."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string(template, {"form": form, "site": site, "org": org, "section": sec}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = FormClass(instance=sec)
        html = render_to_string(template, {"form": form, "site": site, "org": org, "section": sec}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET", "POST"])
def organization_type_option_create_modal(request, site_id: int, org_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    if not (_is_site_admin(request.user, site) or _is_org_admin(request.user, site, org)):
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = OrganizationTypeOptionForm(request.POST)
        if form.is_valid():
            form.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": "Type added."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string('app_site/siteadmin/_type_option_form.html', {"form": form}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = OrganizationTypeOptionForm()
        html = render_to_string('app_site/siteadmin/_type_option_form.html', {"form": form}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET", "POST"])
def organization_tab_edit_modal(request, site_id: int, org_id: int):
    """Edit all sections of the current tab in one modal. Uses prefixed forms per section.
    Overview→Type uses OrganizationSectionTypeForm; others use OrganizationSectionForm.
    """
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    is_site_admin = _is_site_admin(request.user, site)
    is_org_admin = _is_org_admin(request.user, site, org)
    if not (is_site_admin or is_org_admin):
        return HttpResponseForbidden()
    tab = (request.GET.get('tab') or request.POST.get('tab') or 'overview').lower()
    allowed_tabs = {'overview','business','delivery','operations','metrics','review','reports'}
    if tab not in allowed_tabs:
        tab = 'overview'
    # Ensure baseline sections similar to organization_home
    default_titles = {
        'overview': ['Vision','Mission','Value','Strategy','Structure','Type','Summary'],
        'delivery': ['Portfolio','Program','Projects / Products / Services'],
    }
    if tab in default_titles:
        for idx, title in enumerate(default_titles[tab]):
            key = slugify(title)[:64]
            # Look across all records including deleted; restore if necessary
            existing = OrganizationSection.all_objects.filter(organization=org, tab=tab, key=key).first()
            if existing:
                if getattr(existing, 'deleted', False):
                    existing.deleted = False
                    existing.active = True
                    existing.save(update_fields=['deleted', 'active'])
            else:
                # Create with canonical order index
                OrganizationSection.objects.create(organization=org, tab=tab, key=key, title=title, order=idx)
    sections_qs = OrganizationSection.objects.filter(organization=org, tab=tab, active=True).order_by('order','id')
    # Restrict editable set for org admin (site admin sees all)
    if not is_site_admin and is_org_admin:
        allowed_titles = {
            'overview': ['Vision','Mission','Value','Strategy','Structure','Type','Summary'],
            'delivery': ['Portfolio','Program','Projects / Products / Services'],
        }
        allowed = set(allowed_titles.get(tab, []))
        sections = [s for s in sections_qs if s.title in allowed]
    else:
        sections = list(sections_qs)

    # Build forms with unique prefixes
    form_specs = []
    if request.method == 'POST':
        all_valid = True
        for sec in sections:
            prefix = f"sec_{sec.id}"
            if tab == 'overview' and sec.title.lower() == 'type':
                form = OrganizationSectionTypeForm(request.POST, instance=sec, prefix=prefix)
            else:
                form = OrganizationSectionForm(request.POST, instance=sec, prefix=prefix)
            form_specs.append((sec, form))
            if not form.is_valid():
                all_valid = False
        if all_valid:
            for _, form in form_specs:
                form.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": f"{tab.title()} updated."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string('app_site/siteadmin/_org_tab_bulk_edit.html', {"site": site, "org": org, "tab": tab, "form_specs": form_specs}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        for sec in sections:
            prefix = f"sec_{sec.id}"
            if tab == 'overview' and sec.title.lower() == 'type':
                form = OrganizationSectionTypeForm(instance=sec, prefix=prefix)
            else:
                form = OrganizationSectionForm(instance=sec, prefix=prefix)
            form_specs.append((sec, form))
        html = render_to_string('app_site/siteadmin/_org_tab_bulk_edit.html', {"site": site, "org": org, "tab": tab, "form_specs": form_specs}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET", "POST"])
def organization_type_manage_modal(request, site_id: int, org_id: int):
    """Simple list-management modal for type options: reorder, activate/deactivate, delete."""
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    if not (_is_site_admin(request.user, site) or _is_org_admin(request.user, site, org)):
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        opt_id = request.POST.get('id')
        ids = request.POST.getlist('ids')
        if action == 'reorder' and ids:
            # Reorder by list order
            for idx, pk in enumerate(ids):
                OrganizationTypeOption.all_objects.filter(pk=pk).update(position=idx)
        elif action in {'delete','restore'} and ids:
            qs = OrganizationTypeOption.all_objects.filter(pk__in=ids)
            if action == 'delete':
                for o in qs: o.delete()
            else:
                for o in qs:
                    if hasattr(o, 'deleted'):
                        o.deleted = False
                        o.active = True
                        o.save(update_fields=['deleted','active'])
        elif action and opt_id:
            opt = get_object_or_404(OrganizationTypeOption.all_objects, pk=opt_id)
            if action == 'toggle':
                opt.active = not opt.active
                opt.save(update_fields=['active'])
            elif action == 'delete':
                opt.delete()
            elif action == 'restore':
                if hasattr(opt, 'deleted'):
                    opt.deleted = False
                    opt.active = True
                    opt.save(update_fields=['deleted','active'])
            elif action == 'up':
                opt.position = max(0, (opt.position or 0) - 1)
                opt.save(update_fields=['position'])
            elif action == 'down':
                opt.position = (opt.position or 0) + 1
                opt.save(update_fields=['position'])
        # Return refreshed list
        show_bin = request.GET.get('bin') == '1'
        base_qs = OrganizationTypeOption.all_objects
        opts = (base_qs.dead() if show_bin else base_qs.alive()).order_by('position', 'name')
        html = render_to_string(
            'app_0/widgets/_manage_list.html',
            {
                "title": "Manage Types",
                "items": opts,
                "add_url": None if show_bin else request.build_absolute_uri(
                    request.path.replace('/manage/', '/new/')
                ),
                "show_bin": show_bin,
                "site": site,
                "org": org,
            },
            request=request,
        )
        return JsonResponse({"ok": True, "form": html})
    else:
        # Initial GET: return the management table/modal content
        show_bin = request.GET.get('bin') == '1'
        base_qs = OrganizationTypeOption.all_objects
        opts = (base_qs.dead() if show_bin else base_qs.alive()).order_by('position', 'name')
        html = render_to_string(
            'app_0/widgets/_manage_list.html',
            {
                "title": "Manage Types",
                "items": opts,
                "add_url": None if show_bin else request.build_absolute_uri(
                    request.path.replace('/manage/', '/new/')
                ),
                "show_bin": show_bin,
                "site": site,
                "org": org,
            },
            request=request,
        )
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET"])
def organization_settings_modal(request, site_id: int, org_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    if not (_is_site_admin(request.user, site) or _is_org_admin(request.user, site, org)):
        return HttpResponseForbidden()
    html = render_to_string('app_site/siteadmin/_org_settings.html', {"site": site, "org": org}, request=request)
    return JsonResponse({"ok": True, "form": html})

# ---------- Modal CRUD Endpoints ----------
@login_required
@require_http_methods(["GET", "POST"])
def site_edit_modal(request, site_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    if request.method == "POST":
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": "Site updated."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string('app_site/siteadmin/_site_form.html', {"form": form, "site": site}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = SiteForm(instance=site)
        html = render_to_string('app_site/siteadmin/_site_form.html', {"form": form, "site": site}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@user_passes_test(_is_staff)
@require_http_methods(["GET", "POST"])
def site_create_modal(request):
    site = Site()
    if request.method == "POST":
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": "Site created."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string('app_site/siteadmin/_site_form.html', {"form": form, "site": None}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = SiteForm(instance=site)
        html = render_to_string('app_site/siteadmin/_site_form.html', {"form": form, "site": None}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET", "POST"])
def organization_edit_modal(request, site_id: int, org_id: int | None = None):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    org = get_object_or_404(Organization, pk=org_id, site=site) if org_id else Organization(site=site)
    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=org, site=site)
        if form.is_valid():
            org = form.save(commit=False)
            org.site = site
            org.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": "Organization saved."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string('app_site/siteadmin/_organization_form.html', {"form": form, "site": site, "org": org_id and org}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = OrganizationForm(instance=org, site=site)
        html = render_to_string('app_site/siteadmin/_organization_form.html', {"form": form, "site": site, "org": org_id and org}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET", "POST"])
def membership_edit_modal(request, site_id: int, membership_id: int | None = None, role_code: str | None = None, org_id: int | None = None):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    if membership_id:
        membership = get_object_or_404(Membership, pk=membership_id, site=site)
    else:
        membership = Membership(site=site)
    # allow passing role_code and org_id via query params
    if role_code is None:
        role_code = request.GET.get('role_code')
    org = None
    if org_id is None:
        org_id = request.GET.get('org_id')
    if org_id:
        org = get_object_or_404(Organization, pk=org_id, site=site)
    if request.method == "POST":
        form = MembershipForm(request.POST, instance=membership, site=site, role_code=role_code)
        if form.is_valid():
            mem = form.save(commit=False)
            mem.site = site
            if org is not None:
                mem.organization = org
            mem.save()
            html = render_to_string('app_site/siteadmin/_toast_success.html', {"message": "Membership saved."}, request=request)
            return JsonResponse({"ok": True, "toast": html})
        else:
            html = render_to_string('app_site/siteadmin/_membership_form.html', {"form": form, "site": site, "membership": membership_id and membership, "org": org}, request=request)
            return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = MembershipForm(instance=membership, site=site, role_code=role_code)
        html = render_to_string('app_site/siteadmin/_membership_form.html', {"form": form, "site": site, "membership": membership_id and membership, "org": org}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["GET", "POST"])
def org_list_bulk_admin(request, site_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    if request.method == "POST":
        form = BulkOrgAdminForm(request.POST, site=site)
        selected = request.POST.getlist('org_ids')
        if form.is_valid() and selected:
            user = form.cleaned_data['user']
            role = Role.objects.filter(code='orgadmin').first()
            if not role:
                return JsonResponse({"ok": False, "error": "Role orgadmin missing"}, status=400)
            orgs = Organization.objects.filter(site=site, id__in=selected)
            for org in orgs:
                mem, _ = Membership.objects.get_or_create(user=user, site=site, organization=org, role=role)
                mem.active = True
                mem.save()
            return JsonResponse({"ok": True})
        html = render_to_string('app_site/siteadmin/_org_bulk_admin.html', {"form": form, "site": site, "orgs": Organization.objects.filter(site=site)}, request=request)
        return JsonResponse({"ok": False, "form": html}, status=400)
    else:
        form = BulkOrgAdminForm(site=site)
        html = render_to_string('app_site/siteadmin/_org_bulk_admin.html', {"form": form, "site": site, "orgs": Organization.objects.filter(site=site)}, request=request)
        return JsonResponse({"ok": True, "form": html})


@login_required
@require_http_methods(["POST"])
def org_soft_delete(request, site_id: int, org_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    org = get_object_or_404(Organization, pk=org_id, site=site)
    org.delete()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def org_restore(request, site_id: int, org_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    org = get_object_or_404(Organization.all_objects, pk=org_id, site=site)
    org.deleted = False
    org.active = True
    org.save(update_fields=['deleted', 'active'])
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def org_bulk_delete(request, site_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    ids = request.POST.getlist('org_ids') or request.POST.getlist('ids')
    qs = Organization.objects.filter(site=site, id__in=ids)
    count = 0
    for o in qs:
        o.delete()
        count += 1
    return JsonResponse({"ok": True, "count": count})


@login_required
@require_http_methods(["POST"])
def org_bulk_restore(request, site_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    ids = request.POST.getlist('org_ids') or request.POST.getlist('ids')
    qs = Organization.all_objects.filter(site=site, id__in=ids)
    count = 0
    for o in qs:
        o.deleted = False
        o.active = True
        o.save(update_fields=['deleted', 'active'])
        count += 1
    return JsonResponse({"ok": True, "count": count})


@login_required
@require_http_methods(["POST"])
def membership_soft_delete(request, site_id: int, membership_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    membership = get_object_or_404(Membership, pk=membership_id, site=site)
    membership.delete()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def site_soft_delete(request, site_id: int):
    site = get_object_or_404(Site, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    site.delete()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def site_restore(request, site_id: int):
    site = get_object_or_404(Site.all_objects, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    site.deleted = False
    site.active = True
    site.save(update_fields=['deleted', 'active'])
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def site_bulk_delete(request):
    ids = request.POST.getlist('ids')
    qs = Site.objects.filter(id__in=ids)
    # Ensure caller is admin of each site
    for s in list(qs):
        if not _is_site_admin(request.user, s):
            return HttpResponseForbidden()
    for s in qs:
        s.delete()
    return JsonResponse({"ok": True, "count": qs.count()})


@login_required
@require_http_methods(["POST"])
def site_bulk_restore(request):
    ids = request.POST.getlist('ids')
    qs = Site.all_objects.filter(id__in=ids)
    # Ensure caller is admin of each site
    for s in list(qs):
        if not _is_site_admin(request.user, s):
            return HttpResponseForbidden()
    for s in qs:
        s.deleted = False
        s.active = True
        s.save(update_fields=['deleted', 'active'])
    return JsonResponse({"ok": True, "count": qs.count()})


@login_required
@require_http_methods(["POST"])
def site_permadelete(request, site_id: int):
    site = get_object_or_404(Site.all_objects, pk=site_id)
    if not _is_site_admin(request.user, site):
        return HttpResponseForbidden()
    site.deleted = True
    site.active = False
    if hasattr(site, 'blocked'):
        site.blocked = True
        site.save(update_fields=['deleted', 'active', 'blocked'])
    else:
        site.save(update_fields=['deleted', 'active'])
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def site_bulk_permadelete(request):
    ids = request.POST.getlist('ids')
    qs = Site.all_objects.filter(id__in=ids)
    for s in list(qs):
        if not _is_site_admin(request.user, s):
            return HttpResponseForbidden()
    count = 0
    for s in qs:
        s.deleted = True
        s.active = False
        if hasattr(s, 'blocked'):
            s.blocked = True
            s.save(update_fields=['deleted', 'active', 'blocked'])
        else:
            s.save(update_fields=['deleted', 'active'])
        count += 1
    return JsonResponse({"ok": True, "count": count})
