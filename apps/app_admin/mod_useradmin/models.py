from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile({self.user.username})"


class InviteToken(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    email = models.EmailField(blank=True, null=True, help_text="If set, only this email can use the code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    used_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='used_invites')
    used_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"Invite({self.code}, {status})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expires_at is not None and self.expires_at < timezone.now()

    def can_use(self, email: str | None = None):
        if not self.is_active:
            return False
        if self.is_expired:
            return False
        if self.used_by_id:
            return False
        if self.email and email and self.email.lower() != email.lower():
            return False
        return True
