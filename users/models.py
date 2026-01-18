from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom user model for Fakti with additional business profile fields.
    Extends Django's built-in AbstractUser to keep all its authentication features.
    """
    # Basic business profile fields
    business_name = models.CharField(_('Business Name'), max_length=100, blank=True)
    business_address = models.TextField(_('Business Address'), blank=True)
    business_phone = models.CharField(_('Business Phone'), max_length=30, blank=True)
    tax_id = models.CharField(_('Tax ID / Business Registration'), max_length=50, blank=True)
    
    # Business logo
    logo = models.ImageField(_('Business Logo'), upload_to='logos/', blank=True, null=True)
    
    # Settings
    language = models.CharField(
        _('Preferred Language'),
        max_length=2,
        choices=[('ht', _('Haitian Creole')), ('en', _('English'))],
        default='ht'
    )
    
    def __str__(self):
        return self.username
        
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
