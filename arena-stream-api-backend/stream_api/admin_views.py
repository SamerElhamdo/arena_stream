from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import redis
from django.conf import settings

from .models import CustomUser, Subscription, Channel, Event, Category, DeviceLimit
from .serializers import (
    UserSerializer, SubscriptionSerializer, ChannelSerializer, 
    EventSerializer, CategorySerializer, DeviceLimitSerializer
)

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL)
User = get_user_model()


# Admin Permissions
class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# Admin User Management
class AdminUserListView(generics.ListAPIView):
    """
    List all users (Admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return queryset


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific user (Admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class AdminSubscriptionListView(generics.ListCreateAPIView):
    """
    List/Create subscriptions (Admin only)
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class AdminSubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific subscription (Admin only)
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Admin Channel Management
class AdminChannelListView(generics.ListCreateAPIView):
    """
    List/Create channels (Admin only)
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class AdminChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific channel (Admin only)
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Admin Event Management
class AdminEventListView(generics.ListCreateAPIView):
    """
    List/Create events (Admin only)
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class AdminEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific event (Admin only)
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Admin Analytics
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def admin_analytics(request):
    """
    Get comprehensive analytics (Admin only)
    """
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
    
    # Subscription statistics
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(is_active=True).count()
    expired_subscriptions = Subscription.objects.filter(is_active=False).count()
    
    # Channel statistics
    total_channels = Channel.objects.count()
    live_channels = Channel.objects.filter(is_live=True).count()
    total_viewers = Channel.objects.aggregate(total=Count('viewers_count'))['total'] or 0
    
    # Event statistics
    total_events = Event.objects.count()
    live_events = Event.objects.filter(status='Live').count()
    upcoming_events = Event.objects.filter(status='Upcoming').count()
    
    # Device statistics
    total_devices = DeviceLimit.objects.count()
    blocked_devices = DeviceLimit.objects.filter(is_blocked=True).count()
    
    return Response({
        'users': {
            'total': total_users,
            'active': active_users,
            'new_today': new_users_today
        },
        'subscriptions': {
            'total': total_subscriptions,
            'active': active_subscriptions,
            'expired': expired_subscriptions
        },
        'channels': {
            'total': total_channels,
            'live': live_channels,
            'total_viewers': total_viewers
        },
        'events': {
            'total': total_events,
            'live': live_events,
            'upcoming': upcoming_events
        },
        'devices': {
            'total': total_devices,
            'blocked': blocked_devices
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def live_viewers(request):
    """
    Get live viewers information (Admin only)
    """
    try:
        # Get all active sessions from Redis
        active_sessions = redis_client.keys("session:*")
        viewers_data = []
        
        for session_key in active_sessions:
            session_data = redis_client.hgetall(session_key)
            if session_data:
                # Decode bytes to string
                decoded_data = {k.decode(): v.decode() for k, v in session_data.items()}
                
                try:
                    user_id = decoded_data.get('user_id')
                    if user_id:
                        user = User.objects.get(id=user_id)
                        viewers_data.append({
                            'user_id': user.id,
                            'user_email': user.email,
                            'user_name': f"{user.first_name} {user.last_name}",
                            'ip': decoded_data.get('ip', ''),
                            'user_agent': decoded_data.get('user_agent', ''),
                            'started_at': decoded_data.get('started_at', ''),
                            'last_seen': decoded_data.get('last_seen', ''),
                            'session_id': session_key.decode().split(':')[-1]
                        })
                except User.DoesNotExist:
                    continue
        
        return Response({
            'total_active_sessions': len(viewers_data),
            'viewers': viewers_data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def disconnect_user_session(request, user_id, session_id):
    """
    Disconnect specific user session (Admin only)
    """
    try:
        session_key = f"session:{user_id}:{session_id}"
        if redis_client.exists(session_key):
            redis_client.delete(session_key)
            return Response({'message': 'Session disconnected successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def disable_user(request, user_id):
    """
    Disable user account (Admin only)
    """
    try:
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()
        
        # Clear all user sessions
        user_sessions = redis_client.keys(f"session:{user_id}:*")
        for session in user_sessions:
            redis_client.delete(session)
        
        return Response({'message': 'User disabled successfully'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def enable_user(request, user_id):
    """
    Enable user account (Admin only)
    """
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        return Response({'message': 'User enabled successfully'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Category Management
class AdminCategoryListView(generics.ListCreateAPIView):
    """
    List/Create categories (Admin only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific category (Admin only)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Device Management
class AdminDeviceListView(generics.ListAPIView):
    """
    List all devices (Admin only)
    """
    queryset = DeviceLimit.objects.all()
    serializer_class = DeviceLimitSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class AdminDeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific device (Admin only)
    """
    queryset = DeviceLimit.objects.all()
    serializer_class = DeviceLimitSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
