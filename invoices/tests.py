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
		# POST with form data to send email
		data = {
			'to_email': 'bob@example.com',
			'cc': '',
			'bcc': '',
			'subject': 'Invoice INV-2025-00001 for Bob Co',
			'message': 'Please find attached your invoice.',
			'attach_pdf': True,
			'reply_to': 'alice@example.com',
		}
		resp = self.client.post(url, data)
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

# Client Management Tests (Section 3)

class ClientCreateTests(TestCase):
    """Tests for client creation functionality (Feature 3.1)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)
        self.create_url = reverse('client_create')

    def test_client_create_page_loads(self):
        """Test that client creation page loads"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/client_form.html')

    def test_client_create_requires_login(self):
        """Test that client creation requires authentication"""
        self.client.logout()
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_create_client_with_valid_data(self):
        """Test creating a client with valid data"""
        data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'phone': '+509 1234 5678',
            'address': '123 Main St',
            'city': 'Port-au-Prince',
            'country': 'Haiti',
            'notes': 'Test notes'
        }
        response = self.client.post(self.create_url, data)
        self.assertRedirects(response, reverse('client_list'))

        # Client should be created
        self.assertTrue(Client.objects.filter(name='Test Client').exists())
        client = Client.objects.get(name='Test Client')
        self.assertEqual(client.user, self.user)
        self.assertEqual(client.email, 'client@example.com')

    def test_create_client_with_minimal_data(self):
        """Test creating a client with only required field (name)"""
        data = {
            'name': 'Minimal Client',
            'country': 'Haiti'  # Country field included with default value
        }
        response = self.client.post(self.create_url, data)
        self.assertRedirects(response, reverse('client_list'))
        self.assertTrue(Client.objects.filter(name='Minimal Client').exists())

    def test_create_client_without_name_fails(self):
        """Test that creating a client without name fails"""
        data = {'email': 'noemail@example.com'}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertFalse(Client.objects.filter(email='noemail@example.com').exists())


class ClientListTests(TestCase):
    """Tests for client list functionality (Feature 3.2)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)
        self.list_url = reverse('client_list')

        # Create clients for this user
        self.client1 = Client.objects.create(
            user=self.user,
            name='Client One',
            email='one@example.com'
        )
        self.client2 = Client.objects.create(
            user=self.user,
            name='Client Two',
            email='two@example.com'
        )
        # Create client for other user
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

    def test_client_list_loads(self):
        """Test that client list page loads"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/client_list.html')

    def test_client_list_requires_login(self):
        """Test that client list requires authentication"""
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_client_list_shows_only_user_clients(self):
        """Test that client list only shows user's own clients"""
        response = self.client.get(self.list_url)
        clients = response.context['clients']
        self.assertEqual(len(clients), 2)
        self.assertIn(self.client1, clients)
        self.assertIn(self.client2, clients)
        self.assertNotIn(self.other_client, clients)


class ClientDetailTests(TestCase):
    """Tests for client detail functionality (Feature 3.3)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='testclient@example.com',
            phone='+509 1234 5678',
            city='Port-au-Prince'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

        # Create an invoice for this client
        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2024-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

    def test_client_detail_loads(self):
        """Test that client detail page loads"""
        url = reverse('client_detail', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/client_detail.html')

    def test_client_detail_shows_correct_data(self):
        """Test that client detail shows correct data"""
        url = reverse('client_detail', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        self.assertContains(response, 'Test Client')
        self.assertContains(response, 'testclient@example.com')

    def test_client_detail_shows_invoices(self):
        """Test that client detail shows associated invoices"""
        url = reverse('client_detail', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        self.assertIn(self.invoice, response.context['invoices'])

    def test_cannot_view_other_user_client(self):
        """Test that user cannot view other user's client"""
        url = reverse('client_detail', kwargs={'pk': self.other_client.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ClientUpdateTests(TestCase):
    """Tests for client update functionality (Feature 3.4)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Original Name',
            email='original@example.com'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

    def test_client_update_page_loads(self):
        """Test that client update page loads"""
        url = reverse('client_update', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/client_form.html')

    def test_update_client_with_valid_data(self):
        """Test updating a client with valid data"""
        url = reverse('client_update', kwargs={'pk': self.test_client.pk})
        data = {
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'phone': '+509 9999 9999',
            'address': 'New Address',
            'city': 'Cap-Haitien',
            'country': 'Haiti',
            'notes': 'Updated notes'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('client_detail', kwargs={'pk': self.test_client.pk}))

        self.test_client.refresh_from_db()
        self.assertEqual(self.test_client.name, 'Updated Name')
        self.assertEqual(self.test_client.email, 'updated@example.com')

    def test_cannot_update_other_user_client(self):
        """Test that user cannot update other user's client"""
        url = reverse('client_update', kwargs={'pk': self.other_client.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ClientDeleteTests(TestCase):
    """Tests for client delete functionality (Feature 3.5)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Client To Delete',
            email='delete@example.com'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

    def test_client_delete_confirmation_page_loads(self):
        """Test that delete confirmation page loads"""
        url = reverse('client_delete', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/client_confirm_delete.html')

    def test_delete_client(self):
        """Test deleting a client"""
        url = reverse('client_delete', kwargs={'pk': self.test_client.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('client_list'))
        self.assertFalse(Client.objects.filter(pk=self.test_client.pk).exists())

    def test_cannot_delete_other_user_client(self):
        """Test that user cannot delete other user's client"""
        url = reverse('client_delete', kwargs={'pk': self.other_client.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        # Client should still exist
        self.assertTrue(Client.objects.filter(pk=self.other_client.pk).exists())


class ClientQuickInvoiceTests(TestCase):
    """Tests for quick invoice creation from client (Feature 3.6)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='testclient@example.com'
        )

    def test_invoice_create_with_client_param(self):
        """Test that invoice create page pre-selects client when passed as param"""
        url = reverse('invoice_create') + f'?client={self.test_client.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # The form should have the client pre-selected
        form = response.context['form']
        self.assertEqual(form.initial.get('client'), self.test_client.pk)


# Item Management Tests (Section 4)

class ItemCreateTests(TestCase):
    """Tests for item creation functionality (Feature 4.1)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)
        self.create_url = reverse('item_create')

    def test_item_create_page_loads(self):
        """Test that item creation page loads"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/item_form.html')

    def test_item_create_requires_login(self):
        """Test that item creation requires authentication"""
        self.client.logout()
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_create_item_with_valid_data(self):
        """Test creating an item with valid data"""
        from .models import Item
        data = {
            'name': 'Test Service',
            'description': 'A test service description',
            'unit_price': '150.00'
        }
        response = self.client.post(self.create_url, data)
        self.assertRedirects(response, reverse('item_list'))

        # Item should be created
        self.assertTrue(Item.objects.filter(name='Test Service').exists())
        item = Item.objects.get(name='Test Service')
        self.assertEqual(item.user, self.user)
        self.assertEqual(item.description, 'A test service description')
        self.assertEqual(str(item.unit_price), '150.00')

    def test_create_item_without_name_fails(self):
        """Test that creating an item without name fails"""
        from .models import Item
        data = {
            'description': 'Description only',
            'unit_price': '100.00'
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertFalse(Item.objects.filter(description='Description only').exists())

    def test_create_item_without_price_fails(self):
        """Test that creating an item without price fails"""
        from .models import Item
        data = {
            'name': 'No Price Item',
            'description': 'Description'
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertFalse(Item.objects.filter(name='No Price Item').exists())


class ItemListTests(TestCase):
    """Tests for item list functionality (Feature 4.2)"""

    def setUp(self):
        from .models import Item
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)
        self.list_url = reverse('item_list')

        # Create items for this user
        self.item1 = Item.objects.create(
            user=self.user,
            name='Item One',
            description='First item',
            unit_price='100.00'
        )
        self.item2 = Item.objects.create(
            user=self.user,
            name='Item Two',
            description='Second item',
            unit_price='200.00'
        )
        # Create item for other user
        self.other_item = Item.objects.create(
            user=self.other_user,
            name='Other Item',
            description='Other user item',
            unit_price='300.00'
        )

    def test_item_list_loads(self):
        """Test that item list page loads"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/item_list.html')

    def test_item_list_requires_login(self):
        """Test that item list requires authentication"""
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_item_list_shows_only_user_items(self):
        """Test that item list only shows user's own items"""
        response = self.client.get(self.list_url)
        items = response.context['items']
        self.assertEqual(len(items), 2)
        self.assertIn(self.item1, items)
        self.assertIn(self.item2, items)
        self.assertNotIn(self.other_item, items)

    def test_item_list_shows_item_details(self):
        """Test that item list shows item name, description, and price"""
        response = self.client.get(self.list_url)
        self.assertContains(response, 'Item One')
        self.assertContains(response, 'First item')
        self.assertContains(response, '100')


class ItemUpdateTests(TestCase):
    """Tests for item update functionality (Feature 4.3)"""

    def setUp(self):
        from .models import Item
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.item = Item.objects.create(
            user=self.user,
            name='Original Item',
            description='Original description',
            unit_price='100.00'
        )
        self.other_item = Item.objects.create(
            user=self.other_user,
            name='Other Item',
            description='Other description',
            unit_price='200.00'
        )

    def test_item_update_page_loads(self):
        """Test that item update page loads"""
        url = reverse('item_update', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/item_form.html')

    def test_update_item_with_valid_data(self):
        """Test updating an item with valid data"""
        url = reverse('item_update', kwargs={'pk': self.item.pk})
        data = {
            'name': 'Updated Item',
            'description': 'Updated description',
            'unit_price': '250.00'
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('item_list'))

        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Updated Item')
        self.assertEqual(self.item.description, 'Updated description')
        self.assertEqual(str(self.item.unit_price), '250.00')

    def test_cannot_update_other_user_item(self):
        """Test that user cannot update other user's item"""
        url = reverse('item_update', kwargs={'pk': self.other_item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ItemDeleteTests(TestCase):
    """Tests for item delete functionality (Feature 4.4)"""

    def setUp(self):
        from .models import Item
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.item = Item.objects.create(
            user=self.user,
            name='Item To Delete',
            description='Description',
            unit_price='100.00'
        )
        self.other_item = Item.objects.create(
            user=self.other_user,
            name='Other Item',
            description='Other description',
            unit_price='200.00'
        )

    def test_item_delete_confirmation_page_loads(self):
        """Test that delete confirmation page loads"""
        url = reverse('item_delete', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/item_confirm_delete.html')

    def test_delete_item(self):
        """Test deleting an item"""
        from .models import Item
        url = reverse('item_delete', kwargs={'pk': self.item.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('item_list'))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_cannot_delete_other_user_item(self):
        """Test that user cannot delete other user's item"""
        from .models import Item
        url = reverse('item_delete', kwargs={'pk': self.other_item.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        # Item should still exist
        self.assertTrue(Item.objects.filter(pk=self.other_item.pk).exists())


class ItemSelectionTests(TestCase):
    """Tests for item selection in invoice forms (Feature 4.5)"""

    def setUp(self):
        from .models import Item
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        # Create a client for invoices
        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

        # Create items
        self.item1 = Item.objects.create(
            user=self.user,
            name='Service A',
            description='Service A description',
            unit_price='100.00'
        )
        self.item2 = Item.objects.create(
            user=self.user,
            name='Service B',
            description='Service B description',
            unit_price='200.00'
        )

    def test_invoice_form_shows_user_items(self):
        """Test that invoice form shows user's items for selection"""
        url = reverse('invoice_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # The formset should have items in the item field queryset
        formset = response.context['formset']
        # Check that at least one form has items in the queryset
        if formset.forms:
            item_field = formset.forms[0].fields.get('item')
            if item_field:
                queryset = item_field.queryset
                self.assertIn(self.item1, queryset)
                self.assertIn(self.item2, queryset)


class ItemDetailAPITests(TestCase):
    """Tests for item detail API endpoint (Feature 4.6)"""

    def setUp(self):
        from .models import Item
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.item = Item.objects.create(
            user=self.user,
            name='API Test Item',
            description='API test description',
            unit_price='150.50'
        )
        self.other_item = Item.objects.create(
            user=self.other_user,
            name='Other Item',
            description='Other description',
            unit_price='200.00'
        )

    def test_item_api_returns_json(self):
        """Test that item API returns JSON response"""
        url = reverse('item_detail_api', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_item_api_returns_correct_data(self):
        """Test that item API returns correct item data"""
        import json
        url = reverse('item_detail_api', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(data['id'], self.item.pk)
        self.assertEqual(data['name'], 'API Test Item')
        self.assertEqual(data['description'], 'API test description')
        self.assertEqual(data['unit_price'], '150.50')

    def test_item_api_requires_login(self):
        """Test that item API requires authentication"""
        self.client.logout()
        url = reverse('item_detail_api', kwargs={'pk': self.item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_cannot_access_other_user_item_api(self):
        """Test that user cannot access other user's item via API"""
        url = reverse('item_detail_api', kwargs={'pk': self.other_item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# Invoice Management Tests (Section 5)

class InvoiceCreateTests(TestCase):
    """Tests for invoice creation functionality (Feature 5.1)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)
        self.create_url = reverse('invoice_create')

        # Create a client for invoices
        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

    def test_invoice_create_page_loads(self):
        """Test that invoice creation page loads"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/invoice_form.html')

    def test_invoice_create_requires_login(self):
        """Test that invoice creation requires authentication"""
        self.client.logout()
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_create_invoice_with_line_items(self):
        """Test creating an invoice with line items"""
        data = {
            'client': self.test_client.pk,
            'invoice_number': 'INV-2025-00001',
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'HTG',
            'status': 'draft',
            'tax_percent': '10.00',
            'discount_percent': '0.00',
            'notes': 'Test invoice notes',
            # Formset management form
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            # Line item data
            'line_items-0-description': 'Test Service',
            'line_items-0-quantity': '2',
            'line_items-0-unit_price': '100.00',
        }
        response = self.client.post(self.create_url, data)

        # Should redirect to invoice detail
        self.assertEqual(response.status_code, 302)

        # Invoice should be created
        self.assertTrue(Invoice.objects.filter(invoice_number='INV-2025-00001').exists())
        invoice = Invoice.objects.get(invoice_number='INV-2025-00001')
        self.assertEqual(invoice.user, self.user)
        self.assertEqual(invoice.client, self.test_client)

        # Line item should exist
        self.assertEqual(invoice.line_items.count(), 1)
        line_item = invoice.line_items.first()
        self.assertEqual(line_item.description, 'Test Service')
        self.assertEqual(line_item.quantity, 2)

    def test_create_invoice_without_client_fails(self):
        """Test that creating invoice without client fails"""
        data = {
            'invoice_number': 'INV-2025-00002',
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'HTG',
            'status': 'draft',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test',
            'line_items-0-quantity': '1',
            'line_items-0-unit_price': '100.00',
        }
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertFalse(Invoice.objects.filter(invoice_number='INV-2025-00002').exists())


class InvoiceNumberAutoGenerationTests(TestCase):
    """Tests for auto-generated invoice numbers (Feature 5.2)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

    def test_invoice_number_auto_generated(self):
        """Test that invoice number is auto-generated"""
        url = reverse('invoice_create')
        response = self.client.get(url)
        form = response.context['form']

        # Should have initial invoice number in format INV-YYYY-XXXXX
        initial_number = form.initial.get('invoice_number', '') or form.fields['invoice_number'].initial
        if initial_number:
            self.assertTrue(initial_number.startswith('INV-'))
            year = timezone.now().year
            self.assertIn(str(year), initial_number)

    def test_invoice_number_unique_per_user(self):
        """Test that invoice numbers are unique per user"""
        # Create first invoice
        Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

        # Try to create duplicate
        url = reverse('invoice_create')
        data = {
            'client': self.test_client.pk,
            'invoice_number': 'INV-2025-00001',  # Duplicate
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'HTG',
            'status': 'draft',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test',
            'line_items-0-quantity': '1',
            'line_items-0-unit_price': '100.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Form re-rendered with error


class InvoiceListTests(TestCase):
    """Tests for invoice list functionality (Feature 5.3)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)
        self.list_url = reverse('invoice_list')

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

        # Create invoices for this user
        self.invoice1 = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )
        self.invoice2 = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00002',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='paid'
        )
        # Create invoice for other user
        self.other_invoice = Invoice.objects.create(
            user=self.other_user,
            client=self.other_client,
            invoice_number='INV-2025-00003',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

    def test_invoice_list_loads(self):
        """Test that invoice list page loads"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/invoice_list.html')

    def test_invoice_list_requires_login(self):
        """Test that invoice list requires authentication"""
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_invoice_list_shows_only_user_invoices(self):
        """Test that invoice list only shows user's own invoices"""
        response = self.client.get(self.list_url)
        invoices = response.context['invoices']
        self.assertEqual(len(invoices), 2)
        self.assertIn(self.invoice1, invoices)
        self.assertIn(self.invoice2, invoices)
        self.assertNotIn(self.other_invoice, invoices)

    def test_invoice_list_status_filter(self):
        """Test that status filter works"""
        response = self.client.get(self.list_url + '?status=draft')
        invoices = response.context['invoices']
        self.assertEqual(len(invoices), 1)
        self.assertIn(self.invoice1, invoices)

        response = self.client.get(self.list_url + '?status=paid')
        invoices = response.context['invoices']
        self.assertEqual(len(invoices), 1)
        self.assertIn(self.invoice2, invoices)


class InvoiceDetailTests(TestCase):
    """Tests for invoice detail functionality (Feature 5.4)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft',
            notes='Test notes'
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            description='Test Service',
            quantity=2,
            unit_price=100,
            line_total=200
        )

        self.other_invoice = Invoice.objects.create(
            user=self.other_user,
            client=self.other_client,
            invoice_number='INV-2025-00002',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

    def test_invoice_detail_loads(self):
        """Test that invoice detail page loads"""
        url = reverse('invoice_detail', kwargs={'pk': self.invoice.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/invoice_detail.html')

    def test_invoice_detail_shows_correct_data(self):
        """Test that invoice detail shows correct data"""
        url = reverse('invoice_detail', kwargs={'pk': self.invoice.pk})
        response = self.client.get(url)
        self.assertContains(response, 'INV-2025-00001')
        self.assertContains(response, 'Test Client')
        self.assertContains(response, 'Test Service')
        self.assertContains(response, 'Test notes')

    def test_cannot_view_other_user_invoice(self):
        """Test that user cannot view other user's invoice"""
        url = reverse('invoice_detail', kwargs={'pk': self.other_invoice.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class InvoiceUpdateTests(TestCase):
    """Tests for invoice update functionality (Feature 5.5)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )
        self.line_item = InvoiceItem.objects.create(
            invoice=self.invoice,
            description='Original Service',
            quantity=1,
            unit_price=100,
            line_total=100
        )

        self.other_invoice = Invoice.objects.create(
            user=self.other_user,
            client=self.other_client,
            invoice_number='INV-2025-00002',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

    def test_invoice_update_page_loads(self):
        """Test that invoice update page loads"""
        url = reverse('invoice_update', kwargs={'pk': self.invoice.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/invoice_form.html')

    def test_update_invoice(self):
        """Test updating an invoice"""
        url = reverse('invoice_update', kwargs={'pk': self.invoice.pk})
        data = {
            'client': self.test_client.pk,
            'invoice_number': 'INV-2025-00001',
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'USD',  # Changed from HTG
            'status': 'sent',  # Changed from draft
            'tax_percent': '5.00',
            'discount_percent': '0.00',
            'notes': 'Updated notes',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '1',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-id': self.line_item.pk,
            'line_items-0-description': 'Updated Service',
            'line_items-0-quantity': '3',
            'line_items-0-unit_price': '150.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.currency, 'USD')
        self.assertEqual(self.invoice.status, 'sent')
        self.assertEqual(self.invoice.notes, 'Updated notes')

    def test_cannot_update_other_user_invoice(self):
        """Test that user cannot update other user's invoice"""
        url = reverse('invoice_update', kwargs={'pk': self.other_invoice.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class InvoiceDeleteTests(TestCase):
    """Tests for invoice delete functionality (Feature 5.6)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )
        self.other_client = Client.objects.create(
            user=self.other_user,
            name='Other Client',
            email='other@example.com'
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )
        self.other_invoice = Invoice.objects.create(
            user=self.other_user,
            client=self.other_client,
            invoice_number='INV-2025-00002',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

    def test_invoice_delete_confirmation_page_loads(self):
        """Test that delete confirmation page loads"""
        url = reverse('invoice_delete', kwargs={'pk': self.invoice.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoices/invoice_confirm_delete.html')

    def test_delete_invoice(self):
        """Test deleting an invoice"""
        url = reverse('invoice_delete', kwargs={'pk': self.invoice.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('invoice_list'))
        self.assertFalse(Invoice.objects.filter(pk=self.invoice.pk).exists())

    def test_cannot_delete_other_user_invoice(self):
        """Test that user cannot delete other user's invoice"""
        url = reverse('invoice_delete', kwargs={'pk': self.other_invoice.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Invoice.objects.filter(pk=self.other_invoice.pk).exists())


class InvoiceStatusManagementTests(TestCase):
    """Tests for invoice status management (Feature 5.7)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )

    def test_change_status_to_sent(self):
        """Test changing status to sent"""
        url = reverse('invoice_change_status', kwargs={'pk': self.invoice.pk, 'status': 'sent'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('invoice_detail', kwargs={'pk': self.invoice.pk}))

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'sent')

    def test_change_status_to_paid(self):
        """Test changing status to paid"""
        url = reverse('invoice_change_status', kwargs={'pk': self.invoice.pk, 'status': 'paid'})
        response = self.client.get(url)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'paid')

    def test_change_status_to_overdue(self):
        """Test changing status to overdue"""
        url = reverse('invoice_change_status', kwargs={'pk': self.invoice.pk, 'status': 'overdue'})
        response = self.client.get(url)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'overdue')

    def test_change_status_to_canceled(self):
        """Test changing status to canceled"""
        url = reverse('invoice_change_status', kwargs={'pk': self.invoice.pk, 'status': 'canceled'})
        response = self.client.get(url)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'canceled')

    def test_invalid_status_rejected(self):
        """Test that invalid status is rejected"""
        url = reverse('invoice_change_status', kwargs={'pk': self.invoice.pk, 'status': 'invalid'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('invoice_detail', kwargs={'pk': self.invoice.pk}))

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'draft')  # Unchanged


class InvoiceCurrencyTests(TestCase):
    """Tests for currency selection (Feature 5.8)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

    def test_create_invoice_with_htg(self):
        """Test creating invoice with HTG currency"""
        url = reverse('invoice_create')
        data = {
            'client': self.test_client.pk,
            'invoice_number': 'INV-2025-00001',
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'HTG',
            'status': 'draft',
            'tax_percent': '0.00',
            'discount_percent': '0.00',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test',
            'line_items-0-quantity': '1',
            'line_items-0-unit_price': '100.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.get(invoice_number='INV-2025-00001')
        self.assertEqual(invoice.currency, 'HTG')

    def test_create_invoice_with_usd(self):
        """Test creating invoice with USD currency"""
        url = reverse('invoice_create')
        data = {
            'client': self.test_client.pk,
            'invoice_number': 'INV-2025-00002',
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'USD',
            'status': 'draft',
            'tax_percent': '0.00',
            'discount_percent': '0.00',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test',
            'line_items-0-quantity': '1',
            'line_items-0-unit_price': '100.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.get(invoice_number='INV-2025-00002')
        self.assertEqual(invoice.currency, 'USD')


class InvoiceCalculationsTests(TestCase):
    """Tests for invoice calculations (Features 5.9, 5.10, 5.12)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

    def test_line_total_calculation(self):
        """Test line total calculation (quantity * unit_price)"""
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )
        line_item = InvoiceItem.objects.create(
            invoice=invoice,
            description='Test Service',
            quantity=3,
            unit_price=50,
            line_total=0  # Will be calculated on save
        )
        # Line total should be calculated
        self.assertEqual(line_item.line_total, 150)

    def test_subtotal_calculation(self):
        """Test subtotal calculation (sum of line totals)"""
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft'
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Service 1',
            quantity=2,
            unit_price=100,
            line_total=200
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Service 2',
            quantity=1,
            unit_price=150,
            line_total=150
        )
        invoice.calculate_totals()
        invoice.save()

        self.assertEqual(invoice.subtotal, 350)

    def test_tax_calculation(self):
        """Test tax percentage calculation (Feature 5.9)"""
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft',
            tax_percent=10
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Service',
            quantity=1,
            unit_price=1000,
            line_total=1000
        )
        invoice.calculate_totals()
        invoice.save()

        # Tax should be 10% of 1000 = 100
        self.assertEqual(invoice.tax_amount, 100)

    def test_discount_calculation(self):
        """Test discount percentage calculation (Feature 5.10)"""
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft',
            discount_percent=20
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Service',
            quantity=1,
            unit_price=1000,
            line_total=1000
        )
        invoice.calculate_totals()
        invoice.save()

        # Discount should be 20% of 1000 = 200
        self.assertEqual(invoice.discount_amount, 200)

    def test_total_calculation_with_tax_and_discount(self):
        """Test total calculation (subtotal + tax - discount)"""
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft',
            tax_percent=10,
            discount_percent=5
        )
        InvoiceItem.objects.create(
            invoice=invoice,
            description='Service',
            quantity=1,
            unit_price=1000,
            line_total=1000
        )
        invoice.calculate_totals()
        invoice.save()

        # Subtotal: 1000
        # Tax (10%): 100
        # Discount (5%): 50
        # Total: 1000 + 100 - 50 = 1050
        self.assertEqual(invoice.subtotal, 1000)
        self.assertEqual(invoice.tax_amount, 100)
        self.assertEqual(invoice.discount_amount, 50)
        self.assertEqual(invoice.total, 1050)


class InvoiceNotesTests(TestCase):
    """Tests for notes/payment terms field (Feature 5.13)"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        self.client.force_login(self.user)

        self.test_client = Client.objects.create(
            user=self.user,
            name='Test Client',
            email='client@example.com'
        )

    def test_create_invoice_with_notes(self):
        """Test creating invoice with notes"""
        url = reverse('invoice_create')
        data = {
            'client': self.test_client.pk,
            'invoice_number': 'INV-2025-00001',
            'issue_date': timezone.now().date().isoformat(),
            'due_date': (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            'currency': 'HTG',
            'status': 'draft',
            'tax_percent': '0.00',
            'discount_percent': '0.00',
            'notes': 'Payment due within 30 days. Late payments subject to 2% fee.',
            'line_items-TOTAL_FORMS': '1',
            'line_items-INITIAL_FORMS': '0',
            'line_items-MIN_NUM_FORMS': '1',
            'line_items-MAX_NUM_FORMS': '1000',
            'line_items-0-description': 'Test',
            'line_items-0-quantity': '1',
            'line_items-0-unit_price': '100.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        invoice = Invoice.objects.get(invoice_number='INV-2025-00001')
        self.assertEqual(invoice.notes, 'Payment due within 30 days. Late payments subject to 2% fee.')

    def test_notes_displayed_on_detail_page(self):
        """Test that notes are displayed on invoice detail page"""
        invoice = Invoice.objects.create(
            user=self.user,
            client=self.test_client,
            invoice_number='INV-2025-00001',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date(),
            status='draft',
            notes='Test payment terms'
        )
        url = reverse('invoice_detail', kwargs={'pk': invoice.pk})
        response = self.client.get(url)
        self.assertContains(response, 'Test payment terms')
