from django.urls import path
from .views import index, setup, privacy, terms, about

urlpatterns = [
    path('', index, name='index'),
    path('setup/', setup, name='setup'),
    path('privacy/', privacy, name='privacy'),
    path('terms/', terms, name='terms'),
    path('about/', about, name='about'),
]
