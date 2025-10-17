from django.urls import path
from .views import (
    dashboard,
    site_detail,
    organization_detail,
    site_create_modal,
    site_edit_modal,
    organization_edit_modal,
    membership_edit_modal,
        membership_soft_delete,
    org_list_bulk_admin,
    org_soft_delete,
    org_restore,
    org_bulk_delete,
    org_bulk_restore,
    site_soft_delete,
    site_restore,
    site_bulk_delete,
    site_bulk_restore,
    site_permadelete,
    site_bulk_permadelete,
)


urlpatterns = [
    path('', dashboard, name='siteadmin_dashboard'),
    path('<int:site_id>/', site_detail, name='siteadmin_detail'),
    path('<int:site_id>/orgs/<int:org_id>/', organization_detail, name='siteadmin_org_detail'),
    path('<int:site_id>/orgs/bulk-admin/', org_list_bulk_admin, name='siteadmin_org_bulk_admin'),
    path('<int:site_id>/orgs/<int:org_id>/delete/', org_soft_delete, name='siteadmin_org_delete'),
    path('<int:site_id>/orgs/<int:org_id>/restore/', org_restore, name='siteadmin_org_restore'),
    path('<int:site_id>/orgs/bulk-delete/', org_bulk_delete, name='siteadmin_org_bulk_delete'),
    path('<int:site_id>/orgs/bulk-restore/', org_bulk_restore, name='siteadmin_org_bulk_restore'),
    path('<int:site_id>/delete/', site_soft_delete, name='siteadmin_site_delete'),
    path('<int:site_id>/restore/', site_restore, name='siteadmin_site_restore'),
    # site bulk operations
    path('bulk-delete/', site_bulk_delete, name='siteadmin_site_bulk_delete'),
    path('bulk-restore/', site_bulk_restore, name='siteadmin_site_bulk_restore'),
    path('bulk-permadelete/', site_bulk_permadelete, name='siteadmin_site_bulk_permadelete'),
    # modal endpoints
    path('modal/site/new/', site_create_modal, name='siteadmin_site_new_modal'),
    path('<int:site_id>/modal/site/', site_edit_modal, name='siteadmin_site_modal'),
    path('<int:site_id>/modal/org/new/', organization_edit_modal, name='siteadmin_org_new_modal'),
    path('<int:site_id>/modal/org/<int:org_id>/', organization_edit_modal, name='siteadmin_org_edit_modal'),
    path('<int:site_id>/modal/membership/new/', membership_edit_modal, name='siteadmin_membership_new_modal'),
    path('<int:site_id>/modal/membership/<int:membership_id>/', membership_edit_modal, name='siteadmin_membership_edit_modal'),
        path('<int:site_id>/membership/<int:membership_id>/delete/', membership_soft_delete, name='siteadmin_membership_delete'),
    # site permanent delete (soft permanent) for audit trail
    path('<int:site_id>/permadelete/', site_permadelete, name='siteadmin_site_permadelete'),
]
