from django.db import models
from django.utils.text import slugify
from apps.app_0.mod_0.models import BaseModelImpl
from apps.app_admin.mod_siteadmin.models import Site, Organization


class ConstructType(BaseModelImpl):
    """Defines a construct type (e.g., Portfolio, Program, Project, Team, Product, Service, Solution).
    Includes synonyms to allow flexible naming per framework (e.g., Program ≈ ART/Release Train).
    """
    code = models.SlugField(max_length=64, unique=True)
    synonyms = models.TextField(blank=True, help_text='Comma-separated synonyms')

    class Meta(BaseModelImpl.Meta):
        verbose_name = 'Construct Type'
        verbose_name_plural = 'Construct Types'

    def save(self, *args, **kwargs):
        if not self.code and self.name:
            self.code = slugify(self.name)[:64]
        super().save(*args, **kwargs)


class Construct(BaseModelImpl):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='constructs')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='constructs')
    type = models.ForeignKey(ConstructType, on_delete=models.PROTECT, related_name='constructs')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta(BaseModelImpl.Meta):
        verbose_name = 'Construct'
        verbose_name_plural = 'Constructs'
