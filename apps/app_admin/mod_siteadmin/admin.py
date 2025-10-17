from django.contrib import admin

from .models import Site, Organization, Role, Membership


class MembershipInline(admin.TabularInline):
    from .models import Membership
    model = Membership
    extra = 0
    autocomplete_fields = ("user", "role", "organization")
    fields = ("user", "role", "organization", "active")


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]
    fields = ("name", "slug", "description", "active")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "slug", "active")
    list_filter = ("site", "active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]
    fields = ("site", "name", "slug", "description", "active")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "active")
    list_filter = ("code", "active")
    search_fields = ("code", "label")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "site", "organization", "role", "active")
    list_filter = ("site", "organization", "role", "active")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user", "site", "organization", "role")