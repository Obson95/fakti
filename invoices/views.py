from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.conf import settings
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.mail import EmailMessage

from .models import Client, Invoice, InvoiceItem, Item
from .forms import ClientForm, InvoiceForm, InvoiceItemFormSet, ItemForm

import datetime

# Try to import WeasyPrint, which is used for PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_INSTALLED = True
except ImportError:
    # If WeasyPrint is not installed, we'll show a message to the user
    WEASYPRINT_INSTALLED = False


# Client Views
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'invoices/client_list.html'
    context_object_name = 'clients'
    
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'invoices/client_detail.html'
    context_object_name = 'client'
    
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoices'] = self.object.invoices.all()
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'invoices/client_form.html'
    success_url = reverse_lazy('client_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _('Client created successfully.'))
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'invoices/client_form.html'
    
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        return reverse('client_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, _('Client updated successfully.'))
        return super().form_valid(form)


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'invoices/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')
    
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Client deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# Invoice Views
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        queryset = Invoice.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add invoice stats
        invoices = Invoice.objects.filter(user=self.request.user)
        context['total_invoices'] = invoices.count()
        context['draft_count'] = invoices.filter(status='draft').count()
        context['sent_count'] = invoices.filter(status='sent').count()
        context['paid_count'] = invoices.filter(status='paid').count()
        context['overdue_count'] = invoices.filter(status='overdue').count()
        
        # Calculate total amounts
        context['total_amount'] = invoices.aggregate(Sum('total'))['total__sum'] or 0
        context['total_paid'] = invoices.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0
        context['total_outstanding'] = invoices.exclude(status='paid').aggregate(Sum('total'))['total__sum'] or 0
        
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)


@login_required
def create_invoice(request):
    """Create a new invoice with line items"""
    # Check if we have a client ID from the URL
    client_id = request.GET.get('client')
    initial_data = {}
    if client_id:
        try:
            initial_data['client'] = Client.objects.get(pk=client_id, user=request.user).pk
        except Client.DoesNotExist:
            pass
            
    if request.method == 'POST':
        form = InvoiceForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Save the invoice first without committing
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.save()  # Save to get an ID
            
            # Now process the formset with the saved invoice instance
            formset = InvoiceItemFormSet(request.POST, instance=invoice, user=request.user)
            
            if formset.is_valid():
                # Save the formset items
                formset.save()
                
                # Recalculate totals based on saved items
                invoice.calculate_totals()
                invoice.save()
                
                messages.success(request, _('Invoice created successfully.'))
                return redirect('invoice_detail', pk=invoice.pk)
            else:
                # If formset is invalid, delete the invoice to avoid orphaned records
                invoice.delete()
                # Re-render the form with formset errors
        else:
            # Form is invalid - create a temp instance for formset display
            temp_invoice = Invoice(user=request.user)
            formset = InvoiceItemFormSet(request.POST, instance=temp_invoice, user=request.user)
    else:
        # GET request - new form
        form = InvoiceForm(user=request.user, initial=initial_data)
        # Create a temporary unsaved Invoice instance for the formset
        temp_invoice = Invoice(user=request.user)
        formset = InvoiceItemFormSet(instance=temp_invoice, user=request.user)
    
    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'formset': formset,
        'title': _('Create Invoice')
    })


@login_required
def edit_invoice(request, pk):
    """Edit an existing invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        if form.is_valid():
            # Save the form but don't recalculate totals yet
            invoice = form.save()
            
            # Process the formset
            formset = InvoiceItemFormSet(request.POST, instance=invoice, user=request.user)
            if formset.is_valid():
                # Save formset items
                formset.save()
                
                # Now recalculate totals based on all items
                invoice.calculate_totals()
                invoice.save()
                
                messages.success(request, _('Invoice updated successfully.'))
                return redirect('invoice_detail', pk=invoice.pk)
        # If form is invalid, prepare formset for re-rendering
        formset = InvoiceItemFormSet(request.POST, instance=invoice, user=request.user)
    else:
        # GET request - load existing invoice data
        form = InvoiceForm(instance=invoice, user=request.user)
        formset = InvoiceItemFormSet(instance=invoice, user=request.user)
    
    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice,
        'title': _('Edit Invoice')
    })


@login_required
def delete_invoice(request, pk):
    """Delete an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, _('Invoice deleted successfully.'))
        return redirect('invoice_list')
    
    return render(request, 'invoices/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def change_invoice_status(request, pk, status):
    """Change the status of an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    # Validate status
    if status not in [s[0] for s in Invoice.STATUS_CHOICES]:
        messages.error(request, _('Invalid status.'))
        return redirect('invoice_detail', pk=invoice.pk)
    
    invoice.status = status
    invoice.save()
    
    status_labels = dict(Invoice.STATUS_CHOICES)
    messages.success(
        request,
        _('Invoice status changed to %(status)s.') % {'status': status_labels[status].lower()}
    )
    
    return redirect('invoice_detail', pk=invoice.pk)


@login_required
def generate_invoice_pdf(request, pk):
    """Generate a PDF for an invoice"""
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    
    if not WEASYPRINT_INSTALLED:
        messages.error(request, _('PDF generation is not available. Please install WeasyPrint.'))
        return redirect('invoice_detail', pk=invoice.pk)
    
    # Render the invoice template with context
    template = get_template('invoices/invoice_pdf.html')
    context = {
        'invoice': invoice,
        'user': request.user,
        'line_items': invoice.line_items.all(),
        'today': datetime.datetime.now().strftime('%Y-%m-%d'),
    }
    html = template.render(context)
    
    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    
    # Define filename based on client name and invoice number for better organization
    filename = f"invoice_{invoice.invoice_number}_{invoice.client.name.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Generate PDF from HTML with enhanced styling
    HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(
        response,
        # No additional stylesheets needed as we've included them in the template
    )
    
    return response


@login_required
def send_invoice_email(request, pk):
    """Send invoice via email with optional CC/BCC and custom subject/body."""
    from .forms import SendInvoiceEmailForm
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    # Prefill defaults
    default_subject = _('[Fakti] Invoice %(number)s for %(client)s') % {
        'number': invoice.invoice_number,
        'client': invoice.client.name
    }
    default_message = _('Hello %(client)s,\n\nPlease find attached your invoice %(number)s totaling %(total).2f %(currency)s.\n\nThank you,\n%(sender)s') % {
        'client': invoice.client.name,
        'number': invoice.invoice_number,
        'total': invoice.total,
        'currency': invoice.currency,
        'sender': request.user.business_name or request.user.get_full_name() or request.user.username
    }

    if request.method == 'POST':
        form = SendInvoiceEmailForm(request.POST)
        if form.is_valid():
            to_email = form.cleaned_data['to_email']
            cc = form.cleaned_data['cc']
            bcc = form.cleaned_data['bcc']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            attach_pdf = form.cleaned_data['attach_pdf']
            reply_to = form.cleaned_data.get('reply_to')

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', request.user.email),
                to=[to_email],
                cc=cc or None,
                bcc=bcc or None,
                reply_to=[reply_to] if reply_to else None,
            )

            if attach_pdf:
                if not WEASYPRINT_INSTALLED:
                    messages.error(request, _('PDF generation is not available. Please install WeasyPrint.'))
                    return redirect('invoice_detail', pk=invoice.pk)
                template = get_template('invoices/invoice_pdf.html')
                context = {
                    'invoice': invoice,
                    'user': request.user,
                    'line_items': invoice.line_items.all(),
                    'today': datetime.datetime.now().strftime('%Y-%m-%d'),
                }
                html = template.render(context)
                pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
                filename = f"invoice_{invoice.invoice_number}_{invoice.client.name.replace(' ', '_')}.pdf"
                email.attach(filename, pdf_bytes, 'application/pdf')

            try:
                email.send(fail_silently=False)
                messages.success(request, _('Invoice emailed to %(email)s.') % {'email': to_email})
                if invoice.status == 'draft':
                    invoice.status = 'sent'
                    invoice.save()
            except Exception as e:
                messages.error(request, _('Failed to send email: %(error)s') % {'error': str(e)})
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        initial = {
            'to_email': invoice.client.email or '',
            'subject': default_subject,
            'message': default_message,
            'attach_pdf': True,
            'reply_to': request.user.email,
        }
        form = SendInvoiceEmailForm(initial=initial)

    # Render within invoice detail via modal include; fall back to page if JS disabled
    return render(request, 'invoices/send_invoice_email.html', {
        'invoice': invoice,
        'form': form,
    })


# Item Views
class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'invoices/item_list.html'
    context_object_name = 'items'
    
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'invoices/item_form.html'
    success_url = reverse_lazy('item_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _('Item created successfully.'))
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'invoices/item_form.html'
    success_url = reverse_lazy('item_list')
    
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, _('Item updated successfully.'))
        return super().form_valid(form)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    model = Item
    template_name = 'invoices/item_confirm_delete.html'
    success_url = reverse_lazy('item_list')
    
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Item deleted successfully.'))
        return super().delete(request, *args, **kwargs)


@login_required
def item_detail_api(request, pk):
    """API endpoint to get item details"""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    
    data = {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'unit_price': str(item.unit_price)
    }
    
    return JsonResponse(data)


@login_required
def invoice_dashboard(request):
    """Dashboard with invoice statistics"""
    # Get all invoices for this user
    invoices = Invoice.objects.filter(user=request.user)
    
    # Basic counts
    total_invoices = invoices.count()
    draft_count = invoices.filter(status='draft').count()
    sent_count = invoices.filter(status='sent').count()
    paid_count = invoices.filter(status='paid').count()
    overdue_count = invoices.filter(status='overdue').count()
    
    # Calculate totals
    total_amount = invoices.aggregate(Sum('total'))['total__sum'] or 0
    total_paid = invoices.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0
    total_outstanding = invoices.exclude(status='paid').aggregate(Sum('total'))['total__sum'] or 0
    
    # Recent invoices and clients
    recent_invoices = invoices.order_by('-created_at')[:5]
    recent_clients = Client.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Context data
    context = {
        'total_invoices': total_invoices,
        'draft_count': draft_count,
        'sent_count': sent_count,
        'paid_count': paid_count,
        'overdue_count': overdue_count,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'recent_invoices': recent_invoices,
        'recent_clients': recent_clients,
    }
    
    return render(request, 'invoices/dashboard.html', context)
