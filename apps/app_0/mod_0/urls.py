from django.urls import path
from .views import index, setup

urlpatterns = [
    path('', index, name='index'),
    path('setup/', setup, name='setup'),
]
