from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mod_useradmin', '0002_site_role_organization_membership'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InviteToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=64, unique=True)),
                ('email', models.EmailField(blank=True, help_text='If set, only this email can use the code', max_length=254, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('used_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_invites', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
