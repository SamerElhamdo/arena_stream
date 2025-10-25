from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import CustomUser, Subscription, Channel, Event, Category, DeviceLimit

User = get_user_model()


class UserModelTest(TestCase):
    """
    Test cases for CustomUser model
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
    
    def test_user_str_representation(self):
        expected = 'Test User (test@example.com)'
        self.assertEqual(str(self.user), expected)


class SubscriptionModelTest(TestCase):
    """
    Test cases for Subscription model
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_type='Monthly',
            max_devices=3,
            price=29.99,
            expires_at=timezone.now() + timedelta(days=30)
        )
    
    def test_subscription_creation(self):
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.plan_type, 'Monthly')
        self.assertEqual(self.subscription.max_devices, 3)
        self.assertEqual(self.subscription.price, 29.99)
        self.assertTrue(self.subscription.is_active)
    
    def test_subscription_str_representation(self):
        expected = 'test@example.com - Monthly'
        self.assertEqual(str(self.subscription), expected)
    
    def test_subscription_expired_property(self):
        # Test active subscription
        self.assertFalse(self.subscription.is_expired)
        
        # Test expired subscription
        expired_subscription = Subscription.objects.create(
            user=self.user,
            plan_type='Monthly',
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(expired_subscription.is_expired)


class ChannelModelTest(TestCase):
    """
    Test cases for Channel model
    """
    def setUp(self):
        self.category = Category.objects.create(
            name='Football',
            slug='football',
            description='Football channels'
        )
        self.channel = Channel.objects.create(
            name='ESPN',
            slug='espn',
            description='Sports channel',
            source_url='http://example.com/stream.m3u8',
            category=self.category
        )
    
    def test_channel_creation(self):
        self.assertEqual(self.channel.name, 'ESPN')
        self.assertEqual(self.channel.slug, 'espn')
        self.assertEqual(self.channel.category, self.category)
        self.assertFalse(self.channel.is_live)
        self.assertEqual(self.channel.viewers_count, 0)
    
    def test_channel_str_representation(self):
        self.assertEqual(str(self.channel), 'ESPN')


class EventModelTest(TestCase):
    """
    Test cases for Event model
    """
    def setUp(self):
        self.category = Category.objects.create(
            name='Football',
            slug='football'
        )
        self.channel = Channel.objects.create(
            name='ESPN',
            slug='espn',
            source_url='http://example.com/stream.m3u8',
            category=self.category
        )
        self.event = Event.objects.create(
            title='Barcelona vs Real Madrid',
            description='El Clasico match',
            channel=self.channel,
            start_time=timezone.now() + timedelta(hours=2),
            status='Upcoming'
        )
    
    def test_event_creation(self):
        self.assertEqual(self.event.title, 'Barcelona vs Real Madrid')
        self.assertEqual(self.event.channel, self.channel)
        self.assertEqual(self.event.status, 'Upcoming')
        self.assertFalse(self.event.is_live)
    
    def test_event_str_representation(self):
        self.assertEqual(str(self.event), 'Barcelona vs Real Madrid')
    
    def test_event_is_live_property(self):
        # Test upcoming event
        self.assertFalse(self.event.is_live)
        
        # Test live event
        live_event = Event.objects.create(
            title='Live Match',
            channel=self.channel,
            start_time=timezone.now() - timedelta(minutes=30),
            status='Live'
        )
        self.assertTrue(live_event.is_live)


class AuthenticationAPITest(APITestCase):
    """
    Test cases for authentication API endpoints
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
    
    def test_user_registration(self):
        url = reverse('stream_api:register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login(self):
        url = reverse('stream_api:login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        url = reverse('stream_api:login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_logout(self):
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('stream_api:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChannelAPITest(APITestCase):
    """
    Test cases for Channel API endpoints
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Football',
            slug='football'
        )
        self.channel = Channel.objects.create(
            name='ESPN',
            slug='espn',
            source_url='http://example.com/stream.m3u8',
            category=self.category
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_channels(self):
        url = reverse('stream_api:channel-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_channel_detail(self):
        url = reverse('stream_api:channel-detail', kwargs={'pk': self.channel.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'ESPN')


class EventAPITest(APITestCase):
    """
    Test cases for Event API endpoints
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Football',
            slug='football'
        )
        self.channel = Channel.objects.create(
            name='ESPN',
            slug='espn',
            source_url='http://example.com/stream.m3u8',
            category=self.category
        )
        self.event = Event.objects.create(
            title='Barcelona vs Real Madrid',
            channel=self.channel,
            start_time=timezone.now() + timedelta(hours=2),
            status='Upcoming'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_list_events(self):
        url = reverse('stream_api:event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_live_events(self):
        url = reverse('stream_api:event-live')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # No live events in setup
        self.assertEqual(len(response.data['results']), 0)
    
    def test_list_upcoming_events(self):
        url = reverse('stream_api:event-upcoming')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class UserAPITest(APITestCase):
    """
    Test cases for User API endpoints
    """
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan_type='Monthly',
            max_devices=3
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_user_profile(self):
        url = reverse('stream_api:user-profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_get_user_subscription(self):
        url = reverse('stream_api:user-subscription')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan_type'], 'Monthly')
    
    def test_get_user_devices(self):
        url = reverse('stream_api:user-devices')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)


class AdminAPITest(APITestCase):
    """
    Test cases for Admin API endpoints
    """
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            first_name='Admin',
            last_name='User',
            password='adminpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            username='user',
            first_name='Regular',
            last_name='User',
            password='userpass123'
        )
        
        # Get JWT token for admin
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_admin_list_users(self):
        url = reverse('stream_api:admin-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # admin + regular user
    
    def test_admin_get_user_detail(self):
        url = reverse('stream_api:admin-user-detail', kwargs={'pk': self.regular_user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
    
    def test_admin_disable_user(self):
        url = reverse('stream_api:admin-disable-user', kwargs={'user_id': self.regular_user.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if user is disabled
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)
    
    def test_admin_enable_user(self):
        # First disable the user
        self.regular_user.is_active = False
        self.regular_user.save()
        
        url = reverse('stream_api:admin-enable-user', kwargs={'user_id': self.regular_user.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if user is enabled
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)
    
    def test_admin_analytics(self):
        url = reverse('stream_api:admin-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertIn('subscriptions', response.data)
        self.assertIn('channels', response.data)
        self.assertIn('events', response.data)
        self.assertIn('devices', response.data)
    
    def test_non_admin_access_denied(self):
        # Switch to regular user
        refresh = RefreshToken.for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('stream_api:admin-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)