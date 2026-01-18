from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch
from django.core import mail
from django.utils import timezone

from users.models import User
from .models import Client, Invoice, InvoiceItem


class DummyHTML:
	def __init__(self, string=None, base_url=None):
		self.string = string
		self.base_url = base_url

	def write_pdf(self, target=None):
		# If a file-like (HttpResponse) is provided, simulate writing and return None
		if target is not None:
			if hasattr(target, 'write'):
				target.write(b"%PDF-1.4 Dummy")
			return None
		# Otherwise return bytes (used by send_invoice_email)
		return b"%PDF-1.4 Dummy"


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class InvoiceActionsTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='alice',
			email='alice@example.com',
			password='pass1234',
			business_name='Alice LLC'
		)
		self.client.force_login(self.user)

		self.customer = Client.objects.create(
			user=self.user,
			name='Bob Co',
			email='bob@example.com'
		)

		self.invoice = Invoice.objects.create(
			user=self.user,
			client=self.customer,
			invoice_number='INV-2025-00001',
			issue_date=timezone.now().date(),
			due_date=timezone.now().date(),
			status='draft',
			currency='HTG',
		)
		InvoiceItem.objects.create(
			invoice=self.invoice,
			description='Service',
			quantity=1,
			unit_price=100,
			line_total=100,
		)
		# Update totals
		self.invoice.calculate_totals()
		self.invoice.save()

	@patch('invoices.views.WEASYPRINT_INSTALLED', True)
	@patch('invoices.views.HTML', DummyHTML)
	def test_generate_invoice_pdf(self, *mocks):
		url = reverse('invoice_pdf', args=[self.invoice.pk])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp['Content-Type'], 'application/pdf')
		self.assertIn('attachment; filename="invoice_', resp['Content-Disposition'])

	@patch('invoices.views.WEASYPRINT_INSTALLED', True)
	@patch('invoices.views.HTML', DummyHTML)
	def test_send_invoice_email_with_pdf_attachment(self, *mocks):
		url = reverse('invoice_send', args=[self.invoice.pk])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)  # redirect back to detail
		# Email sent
		self.assertEqual(len(mail.outbox), 1)
		message = mail.outbox[0]
		self.assertIn('Invoice INV-2025-00001', message.subject)
		self.assertEqual(message.to, ['bob@example.com'])
		# Has one PDF attachment
		self.assertTrue(message.attachments)
		name, content, mimetype = message.attachments[0]
		self.assertTrue(name.endswith('.pdf'))
		self.assertEqual(mimetype, 'application/pdf')
		self.assertTrue(content.startswith(b'%PDF'))
		# Status updated to sent when it was draft
		self.invoice.refresh_from_db()
		self.assertEqual(self.invoice.status, 'sent')

# Create your tests here.
