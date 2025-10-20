from django.contrib import admin

from .models import Organization, OrganizationSection, OrganizationTypeOption


@admin.register(Organization)
class OrganizationProxyAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "slug", "active")
    list_filter = ("site", "active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(OrganizationSection)
class OrganizationSectionAdmin(admin.ModelAdmin):
    list_display = ("organization", "tab", "title", "order", "active")
    list_filter = ("tab", "organization__site")
    search_fields = ("title", "content")
    list_editable = ("order", "active")


@admin.register(OrganizationTypeOption)
class OrganizationTypeOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "active")
    list_filter = ("active",)
    search_fields = ("name",)
    list_editable = ("position", "active")
