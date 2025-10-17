import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.app_admin.mod_siteadmin.models import Site, Organization, Role, Membership


User = get_user_model()


class Command(BaseCommand):
    help = "Bootstrap a site with organizations and memberships from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument('--create-users', action='store_true', help='Create users if missing with a temp password')
        parser.add_argument('--default-password', type=str, default='Temp#123', help='Default password for created users')

    def _get_or_create_user(self, username: str, email: str | None, create_if_missing: bool, default_password: str):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            if not create_if_missing:
                raise CommandError(f"User '{username}' not found. Use --create-users to create missing users.")
            u = User(username=username, email=email or '')
            u.set_password(default_password)
            u.is_active = True
            u.save()
            return u

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options['json_file'])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        data = json.loads(path.read_text(encoding='utf-8'))

        # Ensure roles exist
        role_siteadmin, _ = Role.objects.get_or_create(code='siteadmin', defaults={'label': 'Site Admin'})
        role_orgadmin, _ = Role.objects.get_or_create(code='orgadmin', defaults={'label': 'Org Admin'})
        role_member, _ = Role.objects.get_or_create(code='member', defaults={'label': 'Member'})

        site_payload: dict[str, Any] = data.get('site') or {}
        if not site_payload:
            raise CommandError("JSON must include 'site' object")

        site, _ = Site.objects.get_or_create(slug=site_payload['slug'], defaults={
            'name': site_payload.get('name', site_payload['slug']),
            'description': site_payload.get('description', ''),
            'active': True,
        })
        # update if provided
        updated = False
        for key in ('name', 'description'):
            if key in site_payload:
                setattr(site, key, site_payload[key]); updated = True
        if updated:
            site.save()

        # Organizations
        org_map: dict[str, Organization] = {}
        for org in data.get('organizations', []):
            o, _ = Organization.objects.get_or_create(site=site, slug=org['slug'], defaults={
                'name': org.get('name', org['slug']),
                'description': org.get('description', ''),
                'active': True,
            })
            if 'name' in org or 'description' in org:
                changed = False
                if 'name' in org:
                    o.name = org['name']; changed = True
                if 'description' in org:
                    o.description = org['description']; changed = True
                if changed:
                    o.save()
            org_map[org['slug']] = o

        # Memberships
        create_users = options['create_users']
        default_password = options['default_password']
        for mem in data.get('memberships', []):
            username = mem['username']
            email = mem.get('email')
            role_code = mem['role']
            org_slug = mem.get('organization')

            user = self._get_or_create_user(username, email, create_users, default_password)
            role = Role.objects.get(code=role_code)
            org = org_map.get(org_slug) if org_slug else None
            Membership.objects.get_or_create(
                user=user, site=site, organization=org, role=role,
                defaults={'active': True}
            )

        self.stdout.write(self.style.SUCCESS(f"Bootstrap complete for site '{site.slug}'."))
