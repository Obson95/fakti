from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin view for the custom user model"""
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Business details'), {
            'fields': ('business_name', 'business_address', 'business_phone', 'tax_id', 'logo')
        }),
        (_('Settings'), {'fields': ('language',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'business_name', 'is_staff')
    search_fields = ('username', 'email', 'business_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'language')
