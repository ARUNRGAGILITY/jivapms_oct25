from django import forms
from django.contrib.auth import authenticate, get_user_model


User = get_user_model()


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank to keep unchanged.")

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes to all widgets
        for name, field in self.fields.items():
            widget = field.widget
            # Boolean fields are rendered as checkboxes
            if isinstance(field, forms.BooleanField):
                existing = widget.attrs.get('class', '')
                widget.attrs['class'] = (existing + ' form-check-input').strip()
            else:
                existing = widget.attrs.get('class', '')
                widget.attrs['class'] = (existing + ' form-control').strip()
        # Ensure password field has proper class
        pw = self.fields.get('password')
        if pw:
            existing = pw.widget.attrs.get('class', '')
            pw.widget.attrs['class'] = (existing + ' form-control').strip()
        # Placeholders for better UX
        placeholders = {
            'username': 'Username',
            'email': 'user@example.com',
            'first_name': 'First name',
            'last_name': 'Last name',
            'password': 'Set a password (optional)'
        }
        for key, text in placeholders.items():
            if key in self.fields:
                self.fields[key].widget.attrs.setdefault('placeholder', text)

        # Reduce intrusive browser autofill on create/edit user forms
        self.fields['username'].widget.attrs.setdefault('autocomplete', 'off')
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.setdefault('autocomplete', 'off')
            self.fields['email'].widget.attrs.setdefault('autocapitalize', 'none')
            self.fields['email'].widget.attrs.setdefault('spellcheck', 'false')
        if 'first_name' in self.fields:
            self.fields['first_name'].widget.attrs.setdefault('autocomplete', 'off')
        if 'last_name' in self.fields:
            self.fields['last_name'].widget.attrs.setdefault('autocomplete', 'off')
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.setdefault('autocomplete', 'new-password')

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user


class BulkCSVForm(forms.Form):
    csv_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 10}), required=False, help_text="CSV rows: username,email,fname,lname,password")
    csv_file = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes and helpful placeholder
        self.fields['csv_text'].widget.attrs['class'] = (self.fields['csv_text'].widget.attrs.get('class', '') + ' form-control font-monospace').strip()
        self.fields['csv_text'].widget.attrs.setdefault('placeholder', (
            'username,email,fname,lname,password\n'
            'alice,alice@example.com,Alice,Lee,Temp#123\n'
            'bob,bob@example.com,Bob,Ray,Temp#123'
        ))
        self.fields['csv_file'].widget.attrs['class'] = (self.fields['csv_file'].widget.attrs.get('class', '') + ' form-control').strip()

    def clean(self):
        data = super().clean()
        if not data.get('csv_text') and not data.get('csv_file'):
            raise forms.ValidationError('Provide CSV text or upload a CSV file.')
        return data


class RegistrationForm(forms.Form):
    invite_code = forms.CharField(max_length=64, label='Invite code')
    email = forms.EmailField(label='Email')
    username = forms.CharField(max_length=150, label='Username')
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (cls + ' form-control').strip()

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            raise forms.ValidationError('Passwords do not match')
        if User.objects.filter(username=data.get('username')).exists():
            raise forms.ValidationError('Username already exists')
        if User.objects.filter(email=data.get('email')).exists():
            raise forms.ValidationError('Email already exists')
        return data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username or email')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (cls + ' form-control').strip()

    def clean(self):
        data = super().clean()
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            # Try email login
            try:
                u = User.objects.get(email__iexact=username)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                user = None
        if not user:
            raise forms.ValidationError('Invalid credentials')
        data['user'] = user
        return data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (cls + ' form-control').strip()
