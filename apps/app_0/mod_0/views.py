from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods


def _is_localhost(request):
    host = request.get_host().split(':')[0]
    return host in {'127.0.0.1', 'localhost'}


def index(request):
    return render(request, 'index.html')


@require_http_methods(["GET", "POST"])
@csrf_protect
def setup(request):
    if not _is_localhost(request):
        return HttpResponseForbidden("Setup is only available on localhost.")

    status = {
        'health_ok': True,
        'pending_migrations': False,
        'superuser_exists': False,
    }

    # Health check: try to ensure connection
    try:
        connection = connections['default']
        connection.ensure_connection()
    except Exception:
        status['health_ok'] = False

    # Pending migrations
    try:
        executor = MigrationExecutor(connections['default'])
        targets = executor.loader.graph.leaf_nodes()
        status['pending_migrations'] = executor.migration_plan(targets) != []
    except Exception:
        # If tables are missing, treat as pending
        status['pending_migrations'] = True

    UserModel = get_user_model()
    status['superuser_exists'] = UserModel.objects.filter(is_superuser=True).exists()

    info = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'migrate':
            try:
                call_command('migrate', interactive=False, verbosity=1)
                info = 'Migrations applied.'
                status['pending_migrations'] = False
            except Exception as e:
                error = f'Error running migrations: {e}'
        elif action == 'create_admin':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            p1 = request.POST.get('password1', '')
            p2 = request.POST.get('password2', '')
            if p1 != p2:
                error = 'Passwords do not match.'
            elif not username or not email or not p1:
                error = 'All fields are required.'
            else:
                try:
                    if not UserModel.objects.filter(username=username).exists():
                        UserModel.objects.create_superuser(username=username, email=email, password=p1)
                        info = 'Admin user created.'
                        status['superuser_exists'] = True
                    else:
                        error = 'Username already exists.'
                except Exception as e:
                    error = f'Error creating admin: {e}'

    context = {
        'status': status,
        'info': info,
        'error': error,
    }
    return render(request, 'app_0/setup.html', context)
