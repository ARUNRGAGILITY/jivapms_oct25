from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationProxyAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "slug", "active")
    list_filter = ("site", "active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
