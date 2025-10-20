from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.app_admin.mod_siteadmin.models import Site, Organization, Membership, Role
from apps.app_site.mod_site.views import _is_org_admin, organization_home, organization_tab_edit_modal


@login_required
def org_portal_home(request):
    """Simple landing that lists organizations where the user is an org admin, grouped by site."""
    role = Role.objects.filter(code='orgadmin').first()
    if not role:
        return HttpResponseForbidden()
    mems = Membership.objects.select_related('site', 'organization').filter(user=request.user, role=role, active=True, organization__isnull=False)
    # Minimal list view; reuse site detail list layout later if desired
    groups = {}
    for m in mems:
        groups.setdefault(m.site, []).append(m.organization)
    return render(request, 'app_site/siteadmin/org_portal_dashboard.html', {"groups": groups})


@login_required
def org_portal_org_home(request, site_id: int, org_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    if not _is_org_admin(request.user, site, org) and not request.user.is_staff:
        return HttpResponseForbidden()
    # Delegate rendering to existing organization_home
    return organization_home(request, site_id=site.id, org_id=org.id)


@login_required
def org_portal_org_edit(request, site_id: int, org_id: int):
    site = get_object_or_404(Site.objects.all(), pk=site_id)
    org = get_object_or_404(Organization.objects.all(), pk=org_id, site=site)
    if not _is_org_admin(request.user, site, org) and not request.user.is_staff:
        return HttpResponseForbidden()
    # Call the bulk tab edit modal; default to overview
    request.GET = request.GET.copy()
    if 'tab' not in request.GET:
        request.GET['tab'] = 'overview'
    return organization_tab_edit_modal(request, site_id=site.id, org_id=org.id)
