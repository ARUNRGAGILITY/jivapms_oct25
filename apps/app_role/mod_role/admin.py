from django.contrib import admin

from .models import Role


@admin.register(Role)
class RoleProxyAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "active")
    list_filter = ("code", "active")
    search_fields = ("code", "label")
