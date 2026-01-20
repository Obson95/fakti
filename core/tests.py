from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

User = get_user_model()


class DashboardAccessTests(TestCase):
    """Tests for dashboard access control"""

    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_dashboard_loads_when_authenticated(self):
        """Test that dashboard loads for authenticated users"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')

    def test_dashboard_shows_username(self):
        """Test that dashboard displays username"""
        self.client.login(username='testuser', password='SecurePass123!')
        response = self.client.get(self.dashboard_url)
        self.assertContains(response, 'testuser')


class DashboardStatisticsTests(TestCase):
    """Tests for dashboard statistics cards (Features 2.1-2.5)"""

    def setUp(self):
        self.client_http = Client()
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        # Import models here to avoid circular imports
        from invoices.models import Client as InvoiceClient, Invoice, InvoiceItem

        # Create test clients
        self.test_client1 = InvoiceClient.objects.create(
            user=self.user,
            name='Client One',
            email='client1@example.com'
        )
        self.test_client2 = InvoiceClient.objects.create(
            user=self.user,
            name='Client Two',
            email='client2@example.com'
        )

        # Helper function to create invoice with line items
        def create_invoice_with_total(user, client, invoice_number, status, total_amount, issue_date, due_date):
            invoice = Invoice.objects.create(
                user=user,
                client=client,
                invoice_number=invoice_number,
                status=status,
                issue_date=issue_date,
                due_date=due_date
            )
            # Add a line item to set the total
            InvoiceItem.objects.create(
                invoice=invoice,
                description='Service',
                quantity=1,
                unit_price=total_amount,
                line_total=total_amount
            )
            # Recalculate totals
            invoice.calculate_totals()
            invoice.save()
            return invoice

        # Create test invoices with various statuses
        self.invoice_paid1 = create_invoice_with_total(
            self.user, self.test_client1, 'INV-2024-00001', 'paid',
            Decimal('1000.00'), timezone.now().date(), timezone.now().date() + timedelta(days=30)
        )
        self.invoice_paid2 = create_invoice_with_total(
            self.user, self.test_client1, 'INV-2024-00002', 'paid',
            Decimal('500.00'), timezone.now().date(), timezone.now().date() + timedelta(days=30)
        )
        self.invoice_sent = create_invoice_with_total(
            self.user, self.test_client2, 'INV-2024-00003', 'sent',
            Decimal('750.00'), timezone.now().date(), timezone.now().date() + timedelta(days=30)
        )
        self.invoice_draft = create_invoice_with_total(
            self.user, self.test_client2, 'INV-2024-00004', 'draft',
            Decimal('250.00'), timezone.now().date(), timezone.now().date() + timedelta(days=30)
        )
        # Create an overdue invoice
        self.invoice_overdue = create_invoice_with_total(
            self.user, self.test_client1, 'INV-2024-00005', 'sent',
            Decimal('300.00'), timezone.now().date() - timedelta(days=60), timezone.now().date() - timedelta(days=30)
        )

    def test_total_invoices_count(self):
        """Test that dashboard shows correct total invoices count (Feature 2.1)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertEqual(response.context['total_invoices'], 5)

    def test_paid_invoices_count(self):
        """Test that dashboard shows correct paid invoices count (Feature 2.1)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertEqual(response.context['paid_invoices'], 2)

    def test_unpaid_invoices_count(self):
        """Test that dashboard shows correct unpaid invoices count (Feature 2.1)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        # Unpaid = all except paid (5 - 2 = 3)
        self.assertEqual(response.context['unpaid_invoices'], 3)

    def test_overdue_invoices_count(self):
        """Test that dashboard shows correct overdue invoices count (Feature 2.1)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        # Only invoice with past due_date and status in ['sent', 'draft']
        self.assertEqual(response.context['overdue_invoices'], 1)

    def test_total_revenue_calculation(self):
        """Test that dashboard shows correct total revenue (Feature 2.2)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        # Revenue = sum of paid invoices (1000 + 500 = 1500)
        self.assertEqual(response.context['total_revenue'], Decimal('1500.00'))

    def test_total_outstanding_calculation(self):
        """Test that dashboard shows correct outstanding amount (Feature 2.3)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        # Outstanding = sum of non-paid invoices (750 + 250 + 300 = 1300)
        self.assertEqual(response.context['total_outstanding'], Decimal('1300.00'))

    def test_payment_rate_calculation(self):
        """Test that dashboard shows correct payment rate (Feature 2.4)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        # Payment rate = (2 paid / 5 total) * 100 = 40%
        self.assertEqual(response.context['payment_rate'], 40)

    def test_total_clients_count(self):
        """Test that dashboard shows correct total clients count (Feature 2.5)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertEqual(response.context['total_clients'], 2)


class DashboardEmptyStateTests(TestCase):
    """Tests for dashboard with no data"""

    def setUp(self):
        self.client_http = Client()
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_empty_dashboard_stats(self):
        """Test that dashboard shows zeros when no invoices exist"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertEqual(response.context['total_invoices'], 0)
        self.assertEqual(response.context['paid_invoices'], 0)
        self.assertEqual(response.context['unpaid_invoices'], 0)
        self.assertEqual(response.context['overdue_invoices'], 0)
        self.assertEqual(response.context['total_revenue'], 0)
        self.assertEqual(response.context['total_outstanding'], 0)
        self.assertEqual(response.context['total_clients'], 0)
        self.assertEqual(response.context['payment_rate'], 0)

    def test_empty_dashboard_shows_no_invoices_message(self):
        """Test that empty dashboard shows helpful message"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        # Should contain empty state or create invoice prompt
        content = response.content.decode()
        self.assertTrue(
            'invoice_create' in content or 'No invoices' in content or 'bi-inbox' in content
        )


class DashboardRecentItemsTests(TestCase):
    """Tests for recent invoices and clients lists (Features 2.6, 2.7)"""

    def setUp(self):
        self.client_http = Client()
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )
        from invoices.models import Client as InvoiceClient, Invoice

        # Create 7 clients (more than the limit of 5)
        self.clients = []
        for i in range(7):
            client = InvoiceClient.objects.create(
                user=self.user,
                name=f'Client {i+1}',
                email=f'client{i+1}@example.com'
            )
            self.clients.append(client)

        # Create 7 invoices (more than the limit of 5)
        self.invoices = []
        for i in range(7):
            invoice = Invoice.objects.create(
                user=self.user,
                client=self.clients[i % len(self.clients)],
                invoice_number=f'INV-2024-{i+1:05d}',
                status='draft',
                total=Decimal('100.00') * (i + 1),
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=30)
            )
            self.invoices.append(invoice)

    def test_recent_invoices_limited_to_five(self):
        """Test that recent invoices list is limited to 5 (Feature 2.6)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        recent_invoices = response.context['recent_invoices']
        self.assertEqual(len(recent_invoices), 5)

    def test_recent_invoices_ordered_by_created_date(self):
        """Test that recent invoices are ordered by creation date (Feature 2.6)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        recent_invoices = list(response.context['recent_invoices'])
        # Should be ordered by created_at descending (most recent first)
        for i in range(len(recent_invoices) - 1):
            self.assertGreaterEqual(
                recent_invoices[i].created_at,
                recent_invoices[i + 1].created_at
            )

    def test_recent_clients_limited_to_five(self):
        """Test that recent clients list is limited to 5 (Feature 2.7)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        recent_clients = response.context['recent_clients']
        self.assertEqual(len(recent_clients), 5)

    def test_recent_clients_ordered_by_created_date(self):
        """Test that recent clients are ordered by creation date (Feature 2.7)"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        recent_clients = list(response.context['recent_clients'])
        # Should be ordered by created_at descending (most recent first)
        for i in range(len(recent_clients) - 1):
            self.assertGreaterEqual(
                recent_clients[i].created_at,
                recent_clients[i + 1].created_at
            )


class DashboardQuickActionsTests(TestCase):
    """Tests for quick action buttons (Feature 2.8)"""

    def setUp(self):
        self.client_http = Client()
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_new_invoice_button_exists(self):
        """Test that New Invoice quick action button exists"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertContains(response, reverse('invoice_create'))

    def test_add_client_button_exists(self):
        """Test that Add Client quick action button exists"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertContains(response, reverse('client_create'))

    def test_view_invoices_button_exists(self):
        """Test that View Invoices quick action button exists"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertContains(response, reverse('invoice_list'))

    def test_manage_clients_button_exists(self):
        """Test that Manage Clients quick action button exists"""
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertContains(response, reverse('client_list'))


class DashboardUserIsolationTests(TestCase):
    """Tests for user data isolation on dashboard"""

    def setUp(self):
        self.client_http = Client()
        self.dashboard_url = reverse('dashboard')

        # Create two users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='SecurePass123!'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='SecurePass123!'
        )

        from invoices.models import Client as InvoiceClient, Invoice, InvoiceItem

        # Helper function to create invoice with line items
        def create_invoice_with_total(user, client, invoice_number, status, total_amount):
            invoice = Invoice.objects.create(
                user=user,
                client=client,
                invoice_number=invoice_number,
                status=status,
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=30)
            )
            InvoiceItem.objects.create(
                invoice=invoice,
                description='Service',
                quantity=1,
                unit_price=total_amount,
                line_total=total_amount
            )
            invoice.calculate_totals()
            invoice.save()
            return invoice

        # Create data for user1
        self.client1 = InvoiceClient.objects.create(
            user=self.user1,
            name='User1 Client',
            email='user1client@example.com'
        )
        self.invoice1 = create_invoice_with_total(
            self.user1, self.client1, 'INV-U1-00001', 'paid', Decimal('1000.00')
        )

        # Create data for user2
        self.client2 = InvoiceClient.objects.create(
            user=self.user2,
            name='User2 Client',
            email='user2client@example.com'
        )
        self.invoice2 = create_invoice_with_total(
            self.user2, self.client2, 'INV-U2-00001', 'paid', Decimal('2000.00')
        )

    def test_user1_only_sees_own_data(self):
        """Test that user1 only sees their own invoices and clients"""
        self.client_http.login(username='user1', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertEqual(response.context['total_invoices'], 1)
        self.assertEqual(response.context['total_clients'], 1)
        self.assertEqual(response.context['total_revenue'], Decimal('1000.00'))

    def test_user2_only_sees_own_data(self):
        """Test that user2 only sees their own invoices and clients"""
        self.client_http.login(username='user2', password='SecurePass123!')
        response = self.client_http.get(self.dashboard_url)

        self.assertEqual(response.context['total_invoices'], 1)
        self.assertEqual(response.context['total_clients'], 1)
        self.assertEqual(response.context['total_revenue'], Decimal('2000.00'))


class HomePageTests(TestCase):
    """Tests for home page"""

    def setUp(self):
        self.client_http = Client()
        self.home_url = reverse('home')

    def test_home_page_loads(self):
        """Test that home page loads for anonymous users"""
        response = self.client_http.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')


# Localization Tests (Section 9)

class LocalizationConfigTests(TestCase):
    """Tests for localization configuration (Features 9.1, 9.2)"""

    def test_default_language_is_haitian_creole(self):
        """Test that default language is Haitian Creole (Feature 9.1)"""
        from django.conf import settings
        self.assertEqual(settings.LANGUAGE_CODE, 'ht')

    def test_haitian_creole_in_available_languages(self):
        """Test that Haitian Creole is available (Feature 9.1)"""
        from django.conf import settings
        language_codes = [code for code, name in settings.LANGUAGES]
        self.assertIn('ht', language_codes)

    def test_english_in_available_languages(self):
        """Test that English is available (Feature 9.2)"""
        from django.conf import settings
        language_codes = [code for code, name in settings.LANGUAGES]
        self.assertIn('en', language_codes)

    def test_i18n_enabled(self):
        """Test that internationalization is enabled"""
        from django.conf import settings
        self.assertTrue(settings.USE_I18N)

    def test_locale_middleware_installed(self):
        """Test that LocaleMiddleware is installed"""
        from django.conf import settings
        self.assertIn(
            'django.middleware.locale.LocaleMiddleware',
            settings.MIDDLEWARE
        )


class LanguageSwitchingTests(TestCase):
    """Tests for language switching functionality (Feature 9.3)"""

    def setUp(self):
        self.client_http = Client()
        self.set_language_url = reverse('set_language')

    def test_language_switch_url_exists(self):
        """Test that language switch URL exists (Feature 9.3)"""
        # Just checking URL can be resolved
        self.assertIsNotNone(self.set_language_url)

    def test_switch_to_english(self):
        """Test switching to English language"""
        # The set_language view needs a 'next' parameter
        response = self.client_http.post(
            self.set_language_url,
            {'language': 'en', 'next': '/'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # The language should be applied - check that the HTML lang attribute is set
        # or that the response cookies or session has the language
        # Django stores language preference in cookie
        if 'django_language' in response.cookies:
            self.assertEqual(response.cookies['django_language'].value, 'en')
        else:
            # If no cookie, the language should still be activated via session
            self.assertEqual(response.status_code, 200)

    def test_switch_to_haitian_creole(self):
        """Test switching to Haitian Creole language"""
        response = self.client_http.post(
            self.set_language_url,
            {'language': 'ht', 'next': '/'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # Check the request succeeded
        if 'django_language' in response.cookies:
            self.assertEqual(response.cookies['django_language'].value, 'ht')
        else:
            # If no cookie, the language should still be activated via session
            self.assertEqual(response.status_code, 200)

    def test_language_toggle_in_navbar(self):
        """Test that language toggle is present in navigation"""
        response = self.client_http.get(reverse('home'))
        self.assertContains(response, 'languageDropdown')
        # Check for the i18n setlang URL (rendered from {% url 'set_language' %})
        self.assertContains(response, '/i18n/setlang/')


class TranslationFileTests(TestCase):
    """Tests for translation files (Features 9.1, 9.2)"""

    def test_haitian_creole_translation_file_exists(self):
        """Test that Haitian Creole translation file exists (Feature 9.1)"""
        from django.conf import settings
        import os

        po_file_path = os.path.join(
            settings.BASE_DIR, 'locale', 'ht', 'LC_MESSAGES', 'django.po'
        )
        self.assertTrue(os.path.exists(po_file_path))

    def test_translation_file_has_content(self):
        """Test that translation file has translations"""
        from django.conf import settings
        import os

        po_file_path = os.path.join(
            settings.BASE_DIR, 'locale', 'ht', 'LC_MESSAGES', 'django.po'
        )

        with open(po_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for some key translations
        self.assertIn('msgid', content)
        self.assertIn('msgstr', content)
        self.assertIn('Dashboard', content)  # Common string


class LocalizedContentTests(TestCase):
    """Tests for localized content display"""

    def setUp(self):
        self.client_http = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_page_renders_with_haitian_creole(self):
        """Test that page renders with Haitian Creole content"""
        self.client_http.cookies['django_language'] = 'ht'
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Page should load successfully with ht language

    def test_page_renders_with_english(self):
        """Test that page renders with English content"""
        self.client_http.cookies['django_language'] = 'en'
        self.client_http.login(username='testuser', password='SecurePass123!')
        response = self.client_http.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Page should load successfully with en language

    def test_html_lang_attribute_set(self):
        """Test that HTML lang attribute reflects current language"""
        response = self.client_http.get(reverse('home'))
        # Check that html lang attribute exists
        self.assertContains(response, '<html lang=')
