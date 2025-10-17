from apps.app_admin.mod_siteadmin.models import Organization as BaseOrganization


class Organization(BaseOrganization):
    class Meta(BaseOrganization.Meta):
        proxy = True
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
