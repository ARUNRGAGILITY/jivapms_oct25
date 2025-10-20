from django.contrib import admin
from .models import InviteToken, UserProfile


@admin.register(InviteToken)
class InviteTokenAdmin(admin.ModelAdmin):
    list_display = ('code', 'email', 'is_active', 'created_at', 'expires_at', 'used_by', 'used_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'email')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'must_change_password')
    list_filter = ('must_change_password',)