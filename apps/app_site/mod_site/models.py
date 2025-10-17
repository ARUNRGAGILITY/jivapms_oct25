from apps.app_admin.mod_siteadmin.models import Site as BaseSite
from apps.app_admin.mod_siteadmin.models import Membership, Role
from django.contrib.auth import get_user_model


class Site(BaseSite):
    class Meta(BaseSite.Meta):
        proxy = True
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'

    def site_admins(self):
        try:
            role = Role.objects.get(code='siteadmin')
        except Role.DoesNotExist:
            return []
        return [m.user for m in Membership.objects.filter(site=self, organization__isnull=True, role=role, active=True)]
