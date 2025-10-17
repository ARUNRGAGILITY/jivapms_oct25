from django.urls import path
from .views import ping, info


urlpatterns = [
    path('ping/', ping, name='api_ping'),
    path('info/', info, name='api_info'),
]
