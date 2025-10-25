from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.cache import cache
import redis
import hmac
import hashlib
import time
import uuid
import requests
import json

from .models import CustomUser, Subscription, Channel, Event, Category, DeviceLimit
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    SubscriptionSerializer, ChannelSerializer, EventSerializer,
    CategorySerializer, DeviceLimitSerializer, StreamPlaySerializer,
    StreamResponseSerializer
)


# Redis connection
redis_client = redis.from_url(settings.REDIS_URL)


def generate_signed_url(channel_slug, secret, ttl=3600):
    """
    Generate HMAC signed HLS URL
    """
    expires = int(time.time()) + ttl
    path = f"/hls/{channel_slug}/index.m3u8"
    message = f"{path}?expires={expires}"
    
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"https://stream.arenastream.com{path}?expires={expires}&sig={signature}"


def enforce_device_limit(user, ip, user_agent, device_info=None):
    """
    Enforce device limit based on user subscription
    """
    try:
        subscription = user.subscription
    except Subscription.DoesNotExist:
        raise PermissionError("No active subscription found")
    
    if not subscription.is_active or subscription.is_expired:
        raise PermissionError("Subscription expired or inactive")
    
    # Generate device identifier
    device_identifier = f"{user.id}_{ip}_{hash(user_agent)}"
    
    # Check active sessions in Redis
    active_sessions = redis_client.keys(f"session:{user.id}:*")
    
    if len(active_sessions) >= subscription.max_devices:
        # Option A: Deny new session
        raise PermissionError("Device limit exceeded")
        
        # Option B: Terminate oldest session (uncomment if needed)
        # if active_sessions:
        #     oldest_session = min(active_sessions, key=lambda x: redis_client.hget(x, 'started_at'))
        #     redis_client.delete(oldest_session)
    
    # Create new session
    session_id = str(uuid.uuid4())
    session_key = f"session:{user.id}:{session_id}"
    
    session_data = {
        'user_id': user.id,
        'ip': ip,
        'user_agent': user_agent,
        'device_info': json.dumps(device_info or {}),
        'started_at': int(time.time()),
        'last_seen': int(time.time())
    }
    
    redis_client.hset(session_key, mapping=session_data)
    redis_client.expire(session_key, 300)  # 5 minutes TTL
    
    return session_id


def spawn_stream(channel):
    """
    Call FFmpeg Controller to start stream
    """
    try:
        response = requests.post(
            f"{settings.STREAMER_URL}/spawn",
            json={
                "slug": channel.slug,
                "source": channel.source_url
            },
            timeout=5
        )
        
        if response.status_code == 200:
            channel.is_live = True
            channel.save()
            return True
    except requests.RequestException:
        pass
    
    return False


# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    User registration endpoint
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    User login endpoint
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """
    User logout endpoint - clear Redis sessions
    """
    user = request.user
    active_sessions = redis_client.keys(f"session:{user.id}:*")
    
    for session in active_sessions:
        redis_client.delete(session)
    
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


# User Views
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get/Update user profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class SubscriptionView(generics.RetrieveUpdateAPIView):
    """
    Get/Update user subscription
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.subscription


# Channel Views
class ChannelListView(generics.ListAPIView):
    """
    List all available channels
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChannelDetailView(generics.RetrieveAPIView):
    """
    Get channel details
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]


# Event Views
class EventListView(generics.ListAPIView):
    """
    List all events
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]


class LiveEventListView(generics.ListAPIView):
    """
    List currently live events
    """
    queryset = Event.objects.filter(status='Live')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]


class UpcomingEventListView(generics.ListAPIView):
    """
    List upcoming events
    """
    queryset = Event.objects.filter(status='Upcoming')
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]


# Stream Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def play_channel(request, pk):
    """
    Get signed HLS URL for channel playback
    """
    try:
        channel = Channel.objects.get(pk=pk)
    except Channel.DoesNotExist:
        return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
    
    user = request.user
    ip = request.META.get('REMOTE_ADDR', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        # Enforce device limit
        session_id = enforce_device_limit(user, ip, user_agent)
        
        # Spawn stream if not active
        if not channel.is_live:
            spawn_stream(channel)
        
        # Generate signed URL
        signed_url = generate_signed_url(channel.slug, settings.HMAC_SECRET)
        
        return Response({
            'channel_id': channel.id,
            'channel_name': channel.name,
            'hls_url': signed_url,
            'expires_in': 3600,
            'session_id': session_id
        }, status=status.HTTP_200_OK)
        
    except PermissionError as e:
        return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def heartbeat(request):
    """
    Update session heartbeat to keep it alive
    """
    session_id = request.data.get('session_id')
    if not session_id:
        return Response({'error': 'Session ID required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    session_key = f"session:{user.id}:{session_id}"
    
    if redis_client.exists(session_key):
        redis_client.hset(session_key, 'last_seen', int(time.time()))
        redis_client.expire(session_key, 300)  # Reset TTL
        return Response({'message': 'Heartbeat updated'}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def disconnect_stream(request):
    """
    Disconnect current stream session
    """
    session_id = request.data.get('session_id')
    if not session_id:
        return Response({'error': 'Session ID required'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    session_key = f"session:{user.id}:{session_id}"
    
    if redis_client.exists(session_key):
        redis_client.delete(session_key)
        return Response({'message': 'Stream disconnected'}, status=status.HTTP_200_OK)
    
    return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


# Category Views
class CategoryListView(generics.ListAPIView):
    """
    List all categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# Device Management Views
class DeviceListView(generics.ListAPIView):
    """
    List user devices
    """
    serializer_class = DeviceLimitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DeviceLimit.objects.filter(user=self.request.user)