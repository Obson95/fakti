from django.urls import path
from . import views

urlpatterns = [
    # Client URLs
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    
    # Item URLs
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/add/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
    path('api/items/<int:pk>/', views.item_detail_api, name='item_detail_api'),
    
    # Invoice URLs
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', views.create_invoice, name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.edit_invoice, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.delete_invoice, name='invoice_delete'),
    path('invoices/<int:pk>/status/<str:status>/', views.change_invoice_status, name='invoice_change_status'),
    path('invoices/<int:pk>/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/send/', views.send_invoice_email, name='invoice_send'),
    
    # Dashboard
    path('dashboard/', views.invoice_dashboard, name='invoice_dashboard'),
]