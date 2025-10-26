from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Subscription, Channel, Event, Category, DeviceLimit, ReStreamTarget, ReStreamSession


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        
        # Create default subscription
        Subscription.objects.create(
            user=user,
            plan_type='Free',
            max_devices=1
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'date_joined', 'is_active', 'subscription')
        read_only_fields = ('id', 'date_joined', 'is_active')
    
    def get_subscription(self, obj):
        try:
            subscription = obj.subscription
            return SubscriptionSerializer(subscription).data
        except Subscription.DoesNotExist:
            return None


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for subscription
    """
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = ('id', 'plan_type', 'max_devices', 'price', 'starts_at', 'expires_at', 'is_active', 'is_expired')
        read_only_fields = ('id', 'starts_at', 'is_active')


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for categories
    """
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'icon', 'description')


class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for channels
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Channel
        fields = ('id', 'name', 'slug', 'description', 'source_url', 'thumbnail', 'is_live', 'viewers_count', 'category', 'category_id', 'created_at')
        read_only_fields = ('id', 'slug', 'viewers_count', 'created_at')
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        channel = Channel.objects.create(**validated_data)
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                channel.category = category
                channel.save()
            except Category.DoesNotExist:
                pass
        return channel


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for events
    """
    channel = ChannelSerializer(read_only=True)
    channel_id = serializers.IntegerField(write_only=True)
    is_live = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = ('id', 'title', 'description', 'channel', 'channel_id', 'start_time', 'end_time', 'status', 'thumbnail', 'is_live', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        channel_id = validated_data.pop('channel_id')
        try:
            channel = Channel.objects.get(id=channel_id)
            validated_data['channel'] = channel
        except Channel.DoesNotExist:
            raise serializers.ValidationError('Invalid channel ID')
        
        return Event.objects.create(**validated_data)


class DeviceLimitSerializer(serializers.ModelSerializer):
    """
    Serializer for device limits
    """
    class Meta:
        model = DeviceLimit
        fields = ('id', 'device_identifier', 'device_name', 'device_type', 'last_used_at', 'is_blocked', 'created_at')
        read_only_fields = ('id', 'last_used_at', 'created_at')


class StreamPlaySerializer(serializers.Serializer):
    """
    Serializer for stream play request
    """
    channel_id = serializers.IntegerField()
    device_info = serializers.DictField(required=False)
    
    def validate_channel_id(self, value):
        try:
            Channel.objects.get(id=value)
        except Channel.DoesNotExist:
            raise serializers.ValidationError('Channel not found')
        return value


class StreamResponseSerializer(serializers.Serializer):
    """
    Serializer for stream play response
    """
    channel_id = serializers.IntegerField()
    channel_name = serializers.CharField()
    hls_url = serializers.URLField()
    expires_in = serializers.IntegerField()
    session_id = serializers.UUIDField()


class ReStreamTargetSerializer(serializers.ModelSerializer):
    """
    Serializer for Re-Stream Targets
    """
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = ReStreamTarget
        fields = ['id', 'name', 'platform', 'platform_display', 'rtmp_url', 'stream_key', 'is_active', 
                  'full_rtmp_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ReStreamSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for Re-Stream Sessions
    """
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    target_name = serializers.CharField(source='target.name', read_only=True)
    duration = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ReStreamSession
        fields = ['id', 'channel', 'channel_name', 'target', 'target_name', 'source_url', 
                  'rtmp_url', 'status', 'status_display', 'process_id', 'error_message', 
                  'started_at', 'stopped_at', 'last_update', 'duration']
        read_only_fields = ['started_at', 'last_update']


class ReStreamStartSerializer(serializers.Serializer):
    """
    Serializer for starting a re-stream
    """
    channel_id = serializers.IntegerField()
    source_url = serializers.URLField(help_text="M3U or HLS source URL")
    target_id = serializers.IntegerField()
    
    def validate_channel_id(self, value):
        """Validate channel exists"""
        try:
            channel = Channel.objects.get(id=value)
        except Channel.DoesNotExist:
            raise serializers.ValidationError('Channel not found')
        return value
    
    def validate_target_id(self, value):
        """Validate target exists"""
        try:
            target = ReStreamTarget.objects.get(id=value)
            if not target.is_active:
                raise serializers.ValidationError('Target is not active')
        except ReStreamTarget.DoesNotExist:
            raise serializers.ValidationError('Target not found')
        return value
