from django.urls import path
from .views import org_portal_home, org_portal_org_home, org_portal_org_edit

urlpatterns = [
    path('', org_portal_home, name='orgadmin_dashboard'),
    path('<int:site_id>/<int:org_id>/home/', org_portal_org_home, name='orgadmin_org_home'),
    path('<int:site_id>/<int:org_id>/edit/', org_portal_org_edit, name='orgadmin_org_edit'),
]
