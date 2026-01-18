from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationTests(TestCase):
    """Tests for user registration functionality (Feature 1.1)"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_register_page_loads(self):
        """Test that registration page loads successfully"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        # Check for form elements (language-agnostic)
        self.assertContains(response, '<form')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_register_form_has_required_fields(self):
        """Test that registration form contains all required fields"""
        response = self.client.get(self.register_url)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="business_name"')
        self.assertContains(response, 'name="password1"')
        self.assertContains(response, 'name="password2"')

    def test_successful_registration(self):
        """Test successful user registration with valid data"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'business_name': 'Test Business',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)

        # Should redirect to login page
        self.assertRedirects(response, reverse('login'))

        # User should be created
        self.assertTrue(User.objects.filter(username='testuser').exists())

        # Check user data
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.business_name, 'Test Business')

    def test_registration_without_business_name(self):
        """Test registration works without optional business name"""
        data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'business_name': '',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='testuser2').exists())

    def test_registration_with_mismatched_passwords(self):
        """Test registration fails with mismatched passwords"""
        data = {
            'username': 'testuser3',
            'email': 'test3@example.com',
            'business_name': 'Test Business',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass456!',
        }
        response = self.client.post(self.register_url, data)

        # Should not redirect, stay on registration page
        self.assertEqual(response.status_code, 200)

        # User should not be created
        self.assertFalse(User.objects.filter(username='testuser3').exists())

        # Should show error
        self.assertContains(response, "password")

    def test_registration_with_duplicate_username(self):
        """Test registration fails with duplicate username"""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='ExistingPass123!'
        )

        data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'business_name': 'New Business',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        # Only one user with this username should exist
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)

    def test_registration_with_weak_password(self):
        """Test registration fails with weak password"""
        data = {
            'username': 'testuser4',
            'email': 'test4@example.com',
            'business_name': 'Test Business',
            'password1': '123',
            'password2': '123',
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser4').exists())

    def test_registration_with_invalid_email(self):
        """Test registration with invalid email format"""
        data = {
            'username': 'testuser5',
            'email': 'invalid-email',
            'business_name': 'Test Business',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testuser5').exists())

    def test_registration_sets_default_language(self):
        """Test that new users get default language (Haitian Creole)"""
        data = {
            'username': 'testuser6',
            'email': 'test6@example.com',
            'business_name': 'Test Business',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        self.client.post(self.register_url, data)

        user = User.objects.get(username='testuser6')
        self.assertEqual(user.language, 'ht')  # Default is Haitian Creole

    def test_register_page_has_login_link(self):
        """Test that registration page has link to login"""
        response = self.client.get(self.register_url)
        self.assertContains(response, reverse('login'))
        self.assertContains(response, 'Already have an account?')


class UserLoginTests(TestCase):
    """Tests for user login functionality (Feature 1.2)"""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_successful_login(self):
        """Test successful login with valid credentials"""
        data = {
            'username': 'testuser',
            'password': 'SecurePass123!',
        }
        response = self.client.post(self.login_url, data)

        # Should redirect after login
        self.assertEqual(response.status_code, 302)

        # User should be authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_wrong_password(self):
        """Test login fails with wrong password"""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword123!',
        }
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_with_nonexistent_user(self):
        """Test login fails with nonexistent username"""
        data = {
            'username': 'nonexistent',
            'password': 'SecurePass123!',
        }
        response = self.client.post(self.login_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserLogoutTests(TestCase):
    """Tests for user logout functionality (Feature 1.3)"""

    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_logout_logs_out_user(self):
        """Test that logout logs out the user"""
        self.client.login(username='testuser', password='SecurePass123!')

        response = self.client.get(self.logout_url)

        # Should redirect or show logged out page
        self.assertIn(response.status_code, [200, 302])

        # User should no longer be authenticated on subsequent request
        response = self.client.get(reverse('home'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class PasswordChangeTests(TestCase):
    """Tests for password change functionality (Feature 1.4)"""

    def setUp(self):
        self.client = Client()
        self.password_change_url = reverse('password_change')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPassword123!'
        )

    def test_password_change_requires_login(self):
        """Test that password change page requires authentication"""
        response = self.client.get(self.password_change_url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_password_change_page_loads_when_authenticated(self):
        """Test that password change page loads for authenticated users"""
        self.client.login(username='testuser', password='OldPassword123!')

        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/password_change.html')

    def test_successful_password_change(self):
        """Test successful password change"""
        self.client.login(username='testuser', password='OldPassword123!')

        data = {
            'old_password': 'OldPassword123!',
            'new_password1': 'NewPassword456!',
            'new_password2': 'NewPassword456!',
        }
        response = self.client.post(self.password_change_url, data)

        # Should redirect to password change done
        self.assertRedirects(response, reverse('password_change_done'))

        # Should be able to login with new password
        self.client.logout()
        login_success = self.client.login(username='testuser', password='NewPassword456!')
        self.assertTrue(login_success)


class PasswordResetTests(TestCase):
    """Tests for password reset functionality (Feature 1.5)"""

    def setUp(self):
        self.client = Client()
        self.password_reset_url = reverse('password_reset')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_password_reset_page_loads(self):
        """Test that password reset page loads"""
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/password_reset.html')

    def test_password_reset_request_with_valid_email(self):
        """Test password reset request with valid email"""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.password_reset_url, data)

        # Should redirect to password reset done
        self.assertRedirects(response, reverse('password_reset_done'))


class AccountDeletionTests(TestCase):
    """Tests for account deletion functionality (Feature 1.6)"""

    def setUp(self):
        self.client = Client()
        self.delete_url = reverse('profile_delete')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_account_deletion_requires_login(self):
        """Test that account deletion requires authentication"""
        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_account_deletion_page_loads(self):
        """Test that account deletion confirmation page loads"""
        self.client.login(username='testuser', password='SecurePass123!')

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile_delete.html')

    def test_successful_account_deletion(self):
        """Test successful account deletion"""
        self.client.login(username='testuser', password='SecurePass123!')

        response = self.client.post(self.delete_url)

        # Should redirect to home
        self.assertRedirects(response, reverse('home'))

        # User should be deleted
        self.assertFalse(User.objects.filter(username='testuser').exists())


class ProfileEditTests(TestCase):
    """Tests for profile editing functionality (Features 1.7, 1.8)"""

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('profile')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_profile_page_requires_login(self):
        """Test that profile page requires authentication"""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_profile_page_loads(self):
        """Test that profile page loads for authenticated users"""
        self.client.login(username='testuser', password='SecurePass123!')

        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_update_personal_info(self):
        """Test updating first name, last name, email (Feature 1.7)"""
        self.client.login(username='testuser', password='SecurePass123!')

        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'business_name': '',
            'business_address': '',
            'business_phone': '',
            'tax_id': '',
            'language': 'ht',
        }
        response = self.client.post(self.profile_url, data)

        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertEqual(self.user.email, 'john.doe@example.com')

    def test_update_business_info(self):
        """Test updating business info (Feature 1.8)"""
        self.client.login(username='testuser', password='SecurePass123!')

        data = {
            'first_name': '',
            'last_name': '',
            'email': 'test@example.com',
            'business_name': 'My Business LLC',
            'business_address': '123 Business St, Port-au-Prince',
            'business_phone': '+509 1234 5678',
            'tax_id': 'TAX-12345',
            'language': 'ht',
        }
        response = self.client.post(self.profile_url, data)

        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.business_name, 'My Business LLC')
        self.assertEqual(self.user.business_address, '123 Business St, Port-au-Prince')
        self.assertEqual(self.user.business_phone, '+509 1234 5678')
        self.assertEqual(self.user.tax_id, 'TAX-12345')


class LogoUploadTests(TestCase):
    """Tests for business logo upload functionality (Feature 1.9)"""

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('profile')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_logo_field_in_profile_form(self):
        """Test that logo upload field exists in profile form"""
        self.client.login(username='testuser', password='SecurePass123!')

        response = self.client.get(self.profile_url)
        self.assertContains(response, 'name="logo"')
        self.assertContains(response, 'type="file"')

    def test_logo_upload(self):
        """Test uploading a business logo"""
        from io import BytesIO
        from PIL import Image

        self.client.login(username='testuser', password='SecurePass123!')

        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        image_file = BytesIO()
        image.save(image_file, 'PNG')
        image_file.name = 'test_logo.png'
        image_file.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile
        logo = SimpleUploadedFile(
            name='test_logo.png',
            content=image_file.read(),
            content_type='image/png'
        )

        data = {
            'first_name': '',
            'last_name': '',
            'email': 'test@example.com',
            'business_name': '',
            'business_address': '',
            'business_phone': '',
            'tax_id': '',
            'language': 'ht',
            'logo': logo,
        }
        response = self.client.post(self.profile_url, data)

        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertTrue(self.user.logo)
        self.assertIn('logos/', self.user.logo.name)


class LanguagePreferenceTests(TestCase):
    """Tests for language preference functionality (Feature 1.10)"""

    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('profile')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='SecurePass123!'
        )

    def test_change_language_to_english(self):
        """Test changing language preference to English"""
        self.client.login(username='testuser', password='SecurePass123!')

        data = {
            'first_name': '',
            'last_name': '',
            'email': 'test@example.com',
            'business_name': '',
            'business_address': '',
            'business_phone': '',
            'tax_id': '',
            'language': 'en',
        }
        response = self.client.post(self.profile_url, data)

        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.language, 'en')

    def test_change_language_to_creole(self):
        """Test changing language preference to Haitian Creole"""
        self.user.language = 'en'
        self.user.save()

        self.client.login(username='testuser', password='SecurePass123!')

        data = {
            'first_name': '',
            'last_name': '',
            'email': 'test@example.com',
            'business_name': '',
            'business_address': '',
            'business_phone': '',
            'tax_id': '',
            'language': 'ht',
        }
        response = self.client.post(self.profile_url, data)

        self.assertRedirects(response, self.profile_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.language, 'ht')
