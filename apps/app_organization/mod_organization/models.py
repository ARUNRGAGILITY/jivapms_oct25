from django.db import models
from django.utils.text import slugify

from apps.app_admin.mod_siteadmin.models import Organization as BaseOrganization
from apps.app_0.mod_0.models import BaseModelImpl


class Organization(BaseOrganization):
    class Meta(BaseOrganization.Meta):
        proxy = True
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'


class OrganizationSection(BaseModelImpl):
    TAB_CHOICES = (
        ('overview', 'Overview'),
        ('business', 'Business'),
        ('delivery', 'Delivery'),
        ('operations', 'Operations'),
        ('metrics', 'Metrics'),
        ('review', 'Review'),
        ('reports', 'Reports'),
    )
    organization = models.ForeignKey(BaseOrganization, on_delete=models.CASCADE, related_name='sections')
    tab = models.CharField(max_length=32, choices=TAB_CHOICES)
    key = models.SlugField(max_length=64)
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta(BaseModelImpl.Meta):
        unique_together = (('organization', 'tab', 'key'),)
        ordering = ('tab', 'order', 'title')
        verbose_name = 'Organization section'
        verbose_name_plural = 'Organization sections'

    def __str__(self):
        return f"{self.organization} [{self.tab}] {self.title}"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = slugify(self.title or 'section')[:64]
        super().save(*args, **kwargs)


class OrganizationTypeOption(BaseModelImpl):
    """Global list of Organization types used by the Overview → Type section.
    Uses BaseModelImpl for soft-delete and ordering via `position`.
    """
    key = models.SlugField(max_length=64, unique=True, blank=True)

    class Meta(BaseModelImpl.Meta):
        verbose_name = 'Organization type option'
        verbose_name_plural = 'Organization type options'

    def save(self, *args, **kwargs):
        # Ensure slug key is set based on name
        if not self.key and (self.name or ''):
            self.key = slugify(self.name)[:64]
        super().save(*args, **kwargs)
