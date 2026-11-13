from django import forms
from django.contrib.auth.models import User
from .db import CATEGORY_METADATA

CATEGORY_CHOICES = [(k, k) for k in CATEGORY_METADATA.keys()]


class DocumentForm(forms.Form):
    title = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Biometric Passport, Auto Insurance Policy',
            'autocomplete': 'off'
        })
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    document_number = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. GBR-992381, POL-882190'
        })
    )
    issuing_authority = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. HM Passport Office, Allianz Global'
        })
    )
    issue_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        })
    )
    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-input',
            'type': 'date'
        }),
        help_text="Leave blank if this is a lifetime or permanent document."
    )
    reminder_days = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=365,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '30'
        }),
        help_text="Days prior to expiry when urgent alert badges trigger."
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 4,
            'placeholder': 'Renewal criteria, locker location, contact phone or website details...'
        })
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input-hidden',
            'id': 'documentFileInput',
            'accept': '.pdf,.jpg,.jpeg,.png,.webp'
        })
    )


class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Eleanor'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Vance'})
    )
    username = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Choose a username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '••••••••••••'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

