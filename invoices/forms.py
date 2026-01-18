from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.forms import inlineformset_factory

from .models import Client, Invoice, InvoiceItem, Item
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class ClientForm(forms.ModelForm):
    """Form for creating and updating clients"""
    
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class InvoiceForm(forms.ModelForm):
    """Form for creating and updating invoices"""
    
    issue_date = forms.DateField(
        label=_("Issue Date"),
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    due_date = forms.DateField(
        label=_("Due Date"),
        initial=lambda: timezone.now().date() + timezone.timedelta(days=30),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = Invoice
        fields = [
            'client', 'invoice_number', 'issue_date', 'due_date', 'currency',
            'tax_percent', 'discount_percent', 'notes', 'status'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If we have a user, filter the client choices to only show this user's clients
        if self.user:
            self.fields['client'].queryset = Client.objects.filter(user=self.user)
            
            # Generate next invoice number
            if not self.instance.pk:  # Only for new invoices
                year = timezone.now().year
                # Count invoices for this user this year and add 1
                count = Invoice.objects.filter(
                    user=self.user, 
                    created_at__year=year
                ).count() + 1
                
                # Format: INV-YYYY-00001
                self.fields['invoice_number'].initial = f"INV-{year}-{count:05d}"

    def clean_invoice_number(self):
        number = self.cleaned_data.get('invoice_number')
        if self.user and number:
            qs = Invoice.objects.filter(user=self.user, invoice_number=number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_("This invoice number is already used for your account."))
        return number


class ItemForm(forms.ModelForm):
    """Form for creating and updating items"""
    
    class Meta:
        model = Item
        fields = ['name', 'description', 'unit_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }


class InvoiceItemForm(forms.ModelForm):
    """Form for invoice items"""
    
    item = forms.ModelChoiceField(
        queryset=Item.objects.none(),
        label=_("Select Item"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control select-item'})
    )
    
    class Meta:
        model = InvoiceItem
        fields = ['item', 'description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If we have a user, filter the items to only show this user's items
        if self.user:
            queryset = Item.objects.filter(user=self.user)
            self.fields['item'].queryset = queryset


# Create a formset for invoice items
BaseInvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)


class InvoiceItemFormSet(BaseInvoiceItemFormSet):
    """Custom formset that passes the user to each form"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Force set initial form classes
        for form in self.forms:
            if 'item' in form.fields:
                form.fields['item'].widget.attrs['class'] = 'form-control select-item'
    
    def _construct_form(self, i, **kwargs):
        # Pass the user to each form in the formset
        kwargs['user'] = self.user
        return super()._construct_form(i, **kwargs)


class SendInvoiceEmailForm(forms.Form):
    """Form used to send an invoice via email with optional CC/BCC and custom message."""
    to_email = forms.EmailField(label=_('To'))
    cc = forms.CharField(label=_('CC'), required=False, help_text=_('Comma or semicolon separated emails'))
    bcc = forms.CharField(label=_('BCC'), required=False, help_text=_('Comma or semicolon separated emails'))
    subject = forms.CharField(label=_('Subject'), max_length=200)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows': 6}))
    attach_pdf = forms.BooleanField(label=_('Attach PDF'), required=False, initial=True)
    reply_to = forms.EmailField(label=_('Reply-To'), required=False)

    @staticmethod
    def _split_emails(value: str):
        if not value:
            return []
        parts = [p.strip() for p in value.replace(';', ',').split(',') if p.strip()]
        # Validate each email
        for p in parts:
            try:
                validate_email(p)
            except ValidationError:
                raise ValidationError(_('%(email)s is not a valid email address'), params={'email': p})
        return parts

    def clean_cc(self):
        return self._split_emails(self.cleaned_data.get('cc'))

    def clean_bcc(self):
        return self._split_emails(self.cleaned_data.get('bcc'))