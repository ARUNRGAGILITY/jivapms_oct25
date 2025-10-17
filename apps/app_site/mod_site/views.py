from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator

from apps.app_admin.mod_siteadmin.models import Site, Organization, Membership, Role
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
            active = form.cleaned_data['active']
            role = Role.objects.filter(code='orgadmin').first()
            if not role:
                return JsonResponse({"ok": False, "error": "Role orgadmin missing"}, status=400)
            orgs = Organization.objects.filter(site=site, id__in=selected)
            for org in orgs:
                mem, _ = Membership.objects.get_or_create(user=user, site=site, organization=org, role=role)
                mem.active = active
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
