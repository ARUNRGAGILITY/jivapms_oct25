from apps.app_admin.mod_siteadmin.models import Role as BaseRole


class Role(BaseRole):
    class Meta(BaseRole.Meta):
        proxy = True
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
