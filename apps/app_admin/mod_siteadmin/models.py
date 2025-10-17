from django.db import models
from django.contrib.auth import get_user_model

from apps.app_0.mod_0.models import BaseModelImpl


User = get_user_model()


class Site(BaseModelImpl):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta(BaseModelImpl.Meta):
        verbose_name = "Site"
        verbose_name_plural = "Sites"

    def __str__(self):
        return self.name


class Organization(BaseModelImpl):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='organizations')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160)
    description = models.TextField(blank=True)

    class Meta(BaseModelImpl.Meta):
        unique_together = (('site', 'slug'), ('site', 'name'))
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return f"{self.site}:{self.name}"


class Role(BaseModelImpl):
    ROLE_CHOICES = (
        ('siteadmin', 'Site Admin'),
        ('orgadmin', 'Org Admin'),
        ('member', 'Member'),
    )
    code = models.CharField(max_length=32, choices=ROLE_CHOICES)
    label = models.CharField(max_length=64)

    class Meta(BaseModelImpl.Meta):
        unique_together = (('code', 'label'),)
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.label or self.get_code_display()


class Membership(BaseModelImpl):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='memberships')

    class Meta(BaseModelImpl.Meta):
        unique_together = (('user', 'site', 'organization', 'role'),)
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    def __str__(self):
        org = self.organization.name if self.organization else '-'
        return f"{self.user} @ {self.site} / {org} as {self.role}"
