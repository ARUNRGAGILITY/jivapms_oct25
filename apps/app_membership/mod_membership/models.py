from apps.app_admin.mod_siteadmin.models import Membership as BaseMembership


class Membership(BaseMembership):
    class Meta(BaseMembership.Meta):
        proxy = True
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'
