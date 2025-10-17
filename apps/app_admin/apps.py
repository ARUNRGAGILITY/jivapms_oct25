from django.apps import AppConfig


class AppAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.app_admin'
    verbose_name = 'Admin Area'

    def ready(self):
        # Ensure nested admin registrations are loaded
        try:
            import apps.app_admin.mod_siteadmin.admin  # noqa: F401
        except Exception:
            # Admin module may not load during certain management commands; ignore.
            pass
        # Seed default roles if table exists
        try:
            from django.db import connection
            if 'app_admin_role' in connection.introspection.table_names():
                from apps.app_admin.mod_siteadmin.models import Role
                for code, label in (
                    ('siteadmin', 'Site Admin'),
                    ('orgadmin', 'Org Admin'),
                    ('member', 'Member'),
                ):
                    Role.objects.get_or_create(code=code, defaults={'label': label})
        except Exception:
            # Ignore if migrations not run yet
            pass
