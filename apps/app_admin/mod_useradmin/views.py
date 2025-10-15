import csv
import io
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import UserForm, BulkCSVForm
from .models import UserProfile


User = get_user_model()


def _is_useradmin(user):
    # Placeholder: restrict to staff or superuser for now
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _ensure_profile(u: User):
    UserProfile.objects.get_or_create(user=u)


@login_required
@user_passes_test(_is_useradmin)
def user_list(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('username')
    if q:
        users = users.filter(username__icontains=q)
    return render(request, 'app_admin/useradmin/list.html', {'users': users, 'q': q})


@login_required
@user_passes_test(_is_useradmin)
@require_http_methods(["GET", "POST"])
def user_create(request):
    form = UserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _ensure_profile(user)
        messages.success(request, 'User created.')
        return redirect('useradmin_list')
    return render(request, 'app_admin/useradmin/form.html', {'form': form, 'mode': 'create'})


@login_required
@user_passes_test(_is_useradmin)
@require_http_methods(["GET", "POST"])
def user_edit(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    form = UserForm(request.POST or None, instance=u)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _ensure_profile(user)
        messages.success(request, 'User updated.')
        return redirect('useradmin_list')
    return render(request, 'app_admin/useradmin/form.html', {'form': form, 'mode': 'edit'})


@login_required
@user_passes_test(_is_useradmin)
@require_http_methods(["POST"])
def user_delete(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    if u.is_superuser:
        messages.error(request, 'Cannot delete superuser.')
    else:
        u.delete()
        messages.success(request, 'User deleted.')
    return redirect('useradmin_list')


@login_required
@user_passes_test(_is_useradmin)
@require_http_methods(["GET", "POST"])
def user_bulk(request):
    form = BulkCSVForm(request.POST or None, request.FILES or None)
    results = []
    if request.method == 'POST' and form.is_valid():
        rows = []
        if form.cleaned_data.get('csv_text'):
            rows = list(csv.reader(io.StringIO(form.cleaned_data['csv_text'])))
        else:
            file = form.cleaned_data['csv_file']
            content = file.read().decode('utf-8', errors='ignore')
            rows = list(csv.reader(io.StringIO(content)))

        for idx, row in enumerate(rows, start=1):
            if not row or len(row) < 5:
                results.append((idx, 'error', 'Invalid row, expected 5 fields: username,email,fname,lname,password'))
                continue
            username, email, fname, lname, password = [c.strip() for c in row[:5]]
            if not username or not email or not password:
                results.append((idx, 'error', 'Username, email and password are required'))
                continue
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email, 'first_name': fname, 'last_name': lname, 'is_active': True
            })
            if not created:
                user.email = email
                user.first_name = fname
                user.last_name = lname
            user.set_password(password)
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.must_change_password = True
            profile.save()
            results.append((idx, 'created' if created else 'updated', username))
        messages.success(request, f'Processed {len(results)} rows.')
    return render(request, 'app_admin/useradmin/bulk.html', {'form': form, 'results': results})
