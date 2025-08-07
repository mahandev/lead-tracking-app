from django.test import TestCase, Client as TestClient
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from .models import Client, Lead
import uuid


class WebhookTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client_model = Client.objects.create(
            user=self.user,
            business_name='Test Business',
            virtual_number='+918045678901'
        )
        self.webhook_token = self.client_model.webhook_token
        self.test_client = TestClient()

    def test_webhook_incoming_completed_call(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        params = {
            'CallSid': 'test_call_001',
            'From': '+919988776655',
            'To': '+918045678901',
            'CallStatus': 'completed',
            'Direction': 'incoming',
            'DialCallDuration': '45',
            'StartTime': '2025-08-07T10:30:00Z',
            'RecordingUrl': 'https://example.com/recording.mp3'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Lead processed')
        self.assertTrue(response.json()['created'])
        
        lead = Lead.objects.get(customer_number='+919988776655')
        self.assertEqual(lead.status, 'contacted')
        self.assertEqual(lead.call_duration, 45)
        self.assertEqual(lead.recording_url, 'https://example.com/recording.mp3')
        self.assertEqual(lead.client, self.client_model)

    def test_webhook_incoming_missed_call(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        params = {
            'CallSid': 'test_call_002',
            'From': '+919988776656',
            'To': '+918045678901',
            'CallStatus': 'no-answer',
            'Direction': 'incoming',
            'DialCallDuration': '0',
            'StartTime': '2025-08-07T10:35:00Z'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        lead = Lead.objects.get(customer_number='+919988776656')
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.call_duration, 0)

    def test_webhook_outgoing_call_filtered(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        params = {
            'CallSid': 'test_call_003',
            'From': '+918045678901',
            'To': '+919988776657',
            'CallStatus': 'completed',
            'Direction': 'outbound',
            'DialCallDuration': '30'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Only incoming calls are processed')
        self.assertEqual(Lead.objects.filter(customer_number='+919988776657').count(), 0)

    def test_webhook_invalid_token(self):
        invalid_token = uuid.uuid4()
        url = reverse('call-webhook', kwargs={'token': invalid_token})
        params = {
            'CallSid': 'test_call_004',
            'From': '+919988776658',
            'Direction': 'incoming'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'Unauthorized')

    def test_webhook_missing_required_fields(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        params = {
            'Direction': 'incoming'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Missing required fields')

    def test_webhook_busy_status_mapping(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        params = {
            'CallSid': 'test_call_005',
            'From': '+919988776659',
            'To': '+918045678901',
            'CallStatus': 'busy',
            'Direction': 'incoming',
            'DialCallDuration': '0'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        lead = Lead.objects.get(customer_number='+919988776659')
        self.assertEqual(lead.status, 'new')

    def test_webhook_failed_status_mapping(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        params = {
            'CallSid': 'test_call_006',
            'From': '+919988776660',
            'To': '+918045678901',
            'CallStatus': 'failed',
            'Direction': 'incoming',
            'DialCallDuration': '0'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        lead = Lead.objects.get(customer_number='+919988776660')
        self.assertEqual(lead.status, 'new')

    def test_webhook_duplicate_call_update(self):
        url = reverse('call-webhook', kwargs={'token': self.webhook_token})
        
        params = {
            'CallSid': 'test_call_007',
            'From': '+919988776661',
            'To': '+918045678901',
            'CallStatus': 'completed',
            'Direction': 'incoming',
            'DialCallDuration': '60',
            'StartTime': '2025-08-07T11:00:00Z',
            'RecordingUrl': 'https://example.com/new_recording.mp3'
        }
        
        response = self.test_client.get(url, params)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['created'])
        
        lead = Lead.objects.get(customer_number='+919988776661')
        self.assertEqual(lead.status, 'contacted')
        self.assertEqual(lead.call_duration, 60)
        self.assertEqual(lead.recording_url, 'https://example.com/new_recording.mp3')


class ClientModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_client_creation(self):
        client = Client.objects.create(
            user=self.user,
            business_name='Test Business',
            virtual_number='+918045678901'
        )
        
        self.assertEqual(client.business_name, 'Test Business')
        self.assertEqual(client.virtual_number, '+918045678901')
        self.assertEqual(client.user, self.user)
        self.assertIsNotNone(client.webhook_token)
        self.assertIsNotNone(client.created_at)

    def test_client_str_method(self):
        client = Client.objects.create(
            user=self.user,
            business_name='Test Business',
            virtual_number='+918045678901'
        )
        
        self.assertEqual(str(client), 'Test Business')


class LeadModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client_model = Client.objects.create(
            user=self.user,
            business_name='Test Business',
            virtual_number='+918045678901'
        )

    def test_lead_creation(self):
        lead = Lead.objects.create(
            client=self.client_model,
            customer_number='+919988776655',
            status='new',
            call_duration=45,
            recording_url='https://example.com/recording.mp3'
        )
        
        self.assertEqual(lead.client, self.client_model)
        self.assertEqual(lead.customer_number, '+919988776655')
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.call_duration, 45)
        self.assertEqual(lead.recording_url, 'https://example.com/recording.mp3')
        self.assertIsNotNone(lead.created_at)

    def test_lead_str_method(self):
        lead = Lead.objects.create(
            client=self.client_model,
            customer_number='+919988776655',
            status='new'
        )
        
        expected_str = f"Lead from +919988776655 for {self.client_model.business_name}"
        self.assertEqual(str(lead), expected_str)

    def test_lead_status_choices(self):
        valid_statuses = ['new', 'contacted', 'converted', 'lost']
        
        for status in valid_statuses:
            lead = Lead.objects.create(
                client=self.client_model,
                customer_number=f'+91998877665{len(valid_statuses)}',
                status=status
            )
            self.assertEqual(lead.status, status)


class DashboardTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client_model = Client.objects.create(
            user=self.user,
            business_name='Test Business',
            virtual_number='+918045678901'
        )
        self.test_client = TestClient()

    def test_dashboard_authentication_required(self):
        response = self.test_client.get('/dashboard/')
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/')

    def test_dashboard_access_with_login(self):
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_analytics_api_authentication_required(self):
        response = self.test_client.get('/analytics/')
        self.assertEqual(response.status_code, 401)

    def test_analytics_api_with_login(self):
        self.test_client.login(username='testuser', password='testpass123')
        response = self.test_client.get('/analytics/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('kpis', data)
        self.assertIn('leads_by_status', data)
        self.assertIn('leads_over_time', data)
