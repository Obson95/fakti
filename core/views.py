from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Home Page View
def home(request):
    """
    Home page view - Shows landing page for non-authenticated users
    """
    return render(request, 'core/home.html')

# Dashboard View
@login_required
def dashboard(request):
    """
    Dashboard view - Shows dashboard for authenticated users
    Retrieves real invoice statistics from the invoices app
    """
    # Import here to avoid circular imports
    from django.db.models import Sum, Count
    from invoices.models import Invoice, Client
    from django.utils import timezone
    
    # Get user's invoices
    invoices = Invoice.objects.filter(user=request.user)
    clients = Client.objects.filter(user=request.user)
    
    # Calculate stats
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(status='paid').count()
    unpaid_invoices = invoices.exclude(status='paid').count()
    overdue_invoices = invoices.filter(
        due_date__lt=timezone.now().date(),
        status__in=['sent', 'draft']
    ).count()
    
    # Calculate revenue
    total_revenue = invoices.filter(status='paid').aggregate(Sum('total'))['total__sum'] or 0
    total_outstanding = invoices.exclude(status='paid').aggregate(Sum('total'))['total__sum'] or 0
    
    # Recent invoices (last 5)
    recent_invoices = invoices.select_related('client').order_by('-created_at')[:5]
    
    # Recent clients (last 5)
    recent_clients = clients.order_by('-created_at')[:5]
    
    # Calculate payment rate percentage
    payment_rate = 0
    if total_invoices > 0:
        payment_rate = round((paid_invoices * 100) / total_invoices)
    
    context = {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices,
        'overdue_invoices': overdue_invoices,
        'total_revenue': total_revenue,
        'total_outstanding': total_outstanding,
        'recent_invoices': recent_invoices,
        'recent_clients': recent_clients,
        'total_clients': clients.count(),
        'payment_rate': payment_rate,
    }
    
    return render(request, 'core/dashboard.html', context)

