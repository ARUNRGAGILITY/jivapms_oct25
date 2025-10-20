import csv
import io
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import UserForm, BulkCSVForm, RegistrationForm, LoginForm, ProfileForm
from .models import UserProfile, InviteToken


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


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['invite_code'].strip()
        email = form.cleaned_data['email'].strip()
        try:
            invite = InviteToken.objects.get(code=code)
        except InviteToken.DoesNotExist:
            messages.error(request, 'Invalid invite code')
        else:
            if not invite.can_use(email):
                messages.error(request, 'Invite code is not valid or expired')
            else:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=email,
                    password=form.cleaned_data['password1'],
                    first_name=form.cleaned_data.get('first_name',''),
                    last_name=form.cleaned_data.get('last_name',''),
                    is_active=True,
                )
                _ensure_profile(user)
                invite.is_active = False
                invite.used_by = user
                invite.used_at = timezone.now()
                invite.save(update_fields=['is_active','used_by','used_at'])
                messages.success(request, 'Account created. You can log in now.')
                return redirect('login')
    return render(request, 'auth/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']
        auth_login(request, user)
        messages.success(request, f'Welcome, {user.first_name or user.username}!')
        next_url = request.GET.get('next') or 'dashboard'
        return redirect(next_url)
    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout(request):
    auth_logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    return render(request, 'auth/dashboard.html')


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated')
        return redirect('profile')
    return render(request, 'auth/profile.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    form = PasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully')
        return redirect('profile')
    return render(request, 'auth/change_password.html', {'form': form})
