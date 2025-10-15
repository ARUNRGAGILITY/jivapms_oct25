from django import forms
from django.contrib.auth import get_user_model


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
