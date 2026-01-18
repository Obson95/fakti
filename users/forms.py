from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """
    Form for user registration with our custom fields
    """
    business_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Your Business Name')}),
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'business_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to password fields (defined in UserCreationForm)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Password')})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': _('Confirm Password')})

class UserProfileForm(forms.ModelForm):
    """
    Form for users to update their profile information
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'business_name',
            'business_address',
            'business_phone',
            'tax_id',
            'logo',
            'language',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'business_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }