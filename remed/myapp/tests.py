from django.test import TestCase
from django.contrib.auth.models import User
from .models import Client, Service

class ClientModelTest(TestCase):
    def test_string_representation(self):
        client = Client(first_name="John", last_name="Doe")
        self.assertEqual(str(client), "John Doe")

class ServiceModelTest(TestCase):
    def test_string_representation(self):
        service = Service(name="Cleaning")
        self.assertEqual(str(service), service.name)

class ViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.user.save()

    def test_admin_dashboard_view(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/admin_dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_proprietor_dashboard_view(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/proprietor_dashboard/')
        self.assertEqual(response.status_code, 200)
