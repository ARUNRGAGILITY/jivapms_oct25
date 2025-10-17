from django.contrib import admin

from .models import Membership


@admin.register(Membership)
class MembershipProxyAdmin(admin.ModelAdmin):
    list_display = ("user", "site", "organization", "role", "active")
    list_filter = ("site", "organization", "role", "active")
    search_fields = ("user__username", "user__email")
    autocomplete_fields = ("user", "site", "organization", "role")
