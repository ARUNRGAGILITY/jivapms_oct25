import os
from django.apps import AppConfig
from django.contrib import admin


class App0Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.app_0'
    verbose_name = 'Common'

    def ready(self):
        admin.site.site_header = os.environ.get('SITE_HEADER', 'JIVAPMS Admin')
        admin.site.site_title = os.environ.get('SITE_NAME', 'JIVAPMS')
        admin.site.index_title = os.environ.get('SITE_TAGLINE', 'Product and Project Management System')
