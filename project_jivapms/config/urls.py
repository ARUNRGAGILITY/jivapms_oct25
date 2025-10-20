from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path
from apps.app_0.mod_0.views import index


def health(_):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('useradmin/', include('apps.app_admin.mod_useradmin.urls')),
    path('api/v1/', include('apis.api_v1.urls')),
    path('siteadmin/', include('apps.app_site.mod_site.urls')),
    path('adminx/', include('apps.app_adminx.urls')),
    path('orgadmin/', include('apps.app_organization.mod_organization.urls')),
    path('health/', health, name='health'),
    path('', include('apps.app_0.mod_0.urls')),
]
