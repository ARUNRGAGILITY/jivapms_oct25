from django.urls import path
from .views import adminx_home

urlpatterns = [
    path('', adminx_home, name='adminx_home'),
]
