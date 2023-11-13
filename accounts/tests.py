# from django.test import TestCase
from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User

class ForgotPasswordTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )

    def test_forgot_password_view_get(self):
        # Test GET request to the forgot_password view
        response = self.client.get(reverse('forgot_password'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/forgot_password.html')
        self.assertContains(response, 'Forgot Password')
        self.assertIsInstance(response.context['form'], PasswordResetForm)

    def test_forgot_password_view_post_valid_form(self):
        # Test POST request to the forgot_password view with a valid form
        data = {'email': 'testuser@example.com'}
        response = self.client.post(reverse('forgot_password'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'password_reset_done.html')

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('your_email@example.com', mail.outbox[0].from_email)
        self.assertIn('password_reset_email.html', mail.outbox[0].message().as_string())

    def test_forgot_password_view_post_invalid_form(self):
        # Test POST request to the forgot_password view with an invalid form
        data = {'email': 'invalid_email'}
        response = self.client.post(reverse('forgot_password'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/forgot_password.html')
        self.assertContains(response, 'This field is required.')  # Adjust based on your form validation

        # Check that no email was sent
        self.assertEqual(len(mail.outbox), 0)
