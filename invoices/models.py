from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Client(models.Model):
    """Client model for storing client information"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name=_("Owner")
    )
    name = models.CharField(_("Name"), max_length=255)
    email = models.EmailField(_("Email"), blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    city = models.CharField(_("City"), max_length=100, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, default="Haiti")
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('client_detail', kwargs={'pk': self.pk})
    
    @property
    def full_address(self):
        """Return the full address as a formatted string"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)
    
    def invoices_count(self):
        """Return the number of invoices for this client"""
        return self.invoices.count()
    
    def total_billed(self):
        """Return the total amount billed to this client"""
        return sum(invoice.total for invoice in self.invoices.all())


class Invoice(models.Model):
    """Invoice model for storing invoice information"""
    
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('paid', _('Paid')),
        ('overdue', _('Overdue')),
        ('canceled', _('Canceled')),
    )
    
    CURRENCY_CHOICES = (
        ('HTG', _('Haitian Gourdes (HTG)')),
        ('USD', _('US Dollars (USD)')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_("Owner")
    )
    client = models.ForeignKey(
        'Client',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_("Client")
    )
    invoice_number = models.CharField(_("Invoice Number"), max_length=50)
    issue_date = models.DateField(_("Issue Date"))
    due_date = models.DateField(_("Due Date"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='HTG'
    )
    subtotal = models.DecimalField(
        _("Subtotal"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax_percent = models.DecimalField(
        _("Tax Percentage"),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        _("Tax Amount"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    discount_percent = models.DecimalField(
        _("Discount Percentage"),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        _("Discount Amount"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        _("Total"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'invoice_number'], name='unique_invoice_number_per_user')
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('invoice_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """Override save to calculate totals before saving"""
        # Only calculate totals if the invoice already exists in DB
        # Otherwise, set defaults and calculate after line items are added
        if self.pk:
            self.calculate_totals()
        else:
            # Set default values for new invoices
            self.subtotal = 0
            self.tax_amount = 0
            self.discount_amount = 0
            self.total = 0
            
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate invoice subtotal, tax, discount, and total"""
        # Calculate subtotal from line items
        if self.pk:  # Only calculate if invoice is already saved
            line_items = self.line_items.all()
            self.subtotal = sum(item.line_total for item in line_items)
        
        # Calculate tax amount
        if self.tax_percent:
            self.tax_amount = self.subtotal * (self.tax_percent / 100)
        else:
            self.tax_amount = 0
            
        # Calculate discount amount
        if self.discount_percent:
            self.discount_amount = self.subtotal * (self.discount_percent / 100)
        else:
            self.discount_amount = 0
            
        # Calculate final total
        self.total = self.subtotal + self.tax_amount - self.discount_amount
        
    def is_overdue(self):
        """Check if invoice is overdue"""
        from django.utils import timezone
        return self.status != 'paid' and self.due_date < timezone.now().date()


class Item(models.Model):
    """Model for storing predefined items that can be added to invoices"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Owner")
    )
    name = models.CharField(_("Name"), max_length=255)
    description = models.CharField(_("Description"), max_length=255)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.unit_price})"


class InvoiceItem(models.Model):
    """Model for storing invoice line items"""
    
    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.CASCADE,
        related_name='line_items',
        verbose_name=_("Invoice")
    )
    item = models.ForeignKey(
        'Item',
        on_delete=models.SET_NULL,
        related_name='invoice_items',
        verbose_name=_("Item"),
        null=True,
        blank=True
    )
    description = models.CharField(_("Description"), max_length=255)
    quantity = models.DecimalField(_("Quantity"), max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=10, decimal_places=2)
    line_total = models.DecimalField(_("Line Total"), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _("Invoice Item")
        verbose_name_plural = _("Invoice Items")
    
    def __str__(self):
        return f"{self.description} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """Calculate line total before saving"""
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update the parent invoice totals, but avoid circular saving
        # Get the invoice instance from the database again to avoid recursion
        from django.db import connection
        if connection.in_atomic_block:
            # Don't trigger a save during atomic operations (like formset saving)
            return
            
        # Only update the parent invoice if it already exists
        if self.invoice_id:
            Invoice = self.invoice.__class__
            invoice = Invoice.objects.get(pk=self.invoice_id)
            invoice.calculate_totals()
            invoice.save()
