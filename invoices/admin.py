from django.contrib import admin
from .models import Client, Invoice, InvoiceItem, Item


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'email', 'phone', 'country', 'created_at')
    list_filter = ('created_at', 'country')
    search_fields = ('name', 'email', 'phone', 'address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'country')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'client', 'issue_date', 'due_date', 'status', 'total')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'client__name', 'notes')
    readonly_fields = ('subtotal', 'tax_amount', 'discount_amount', 'total', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'client', 'invoice_number', 'issue_date', 'due_date', 'status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_percent', 'tax_amount', 'discount_percent', 'discount_amount', 'total')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    inlines = [InvoiceItemInline]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price', 'line_total')
    list_filter = ('invoice',)
    search_fields = ('description', 'invoice__invoice_number')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description', 'unit_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
