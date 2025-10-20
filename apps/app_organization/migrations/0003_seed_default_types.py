from django.db import migrations
from django.utils.text import slugify


def seed_types(apps, schema_editor):
    Type = apps.get_model('app_organization', 'OrganizationTypeOption')
    defaults = [
        ('Project-based', 10),
        ('Product-based', 20),
        ('Service-based', 30),
        ('Consulting-based', 40),
        ('Custom', 50),
        ('Hybrid Type', 60),
    ]
    for name, pos in defaults:
        # Historical models do not have custom managers; use default manager
        key = slugify(name)[:64]
        existing = Type.objects.filter(name=name).first() or (
            Type.objects.filter(**({'key': key} if 'key' in [f.name for f in Type._meta.fields] else {})).first()
        )
        if existing:
            # Update basic fields if present
            existing.position = pos
            existing.active = True
            # If the model has deleted field in historical state, clear it
            if hasattr(existing, 'deleted'):
                setattr(existing, 'deleted', False)
            if hasattr(existing, 'key') and not getattr(existing, 'key'):
                setattr(existing, 'key', key)
            existing.save()
        else:
            kwargs = {'name': name, 'position': pos, 'active': True}
            if 'key' in [f.name for f in Type._meta.fields]:
                kwargs['key'] = key
            obj = Type(**kwargs)
            if hasattr(obj, 'deleted'):
                setattr(obj, 'deleted', False)
            obj.save()


def unseed_types(apps, schema_editor):
    # Do not remove seeded data on reverse; keep idempotent
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('app_organization', '0002_organizationtypeoption'),
    ]

    operations = [
        migrations.RunPython(seed_types, unseed_types),
    ]
