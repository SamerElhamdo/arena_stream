from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    """
    Custom User model for ArenaStream platform
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'custom_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Category(models.Model):
    """
    Channel categories (Football, Basketball, Tennis, etc.)
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Subscription(models.Model):
    """
    User subscription plans
    """
    PLAN_CHOICES = [
        ('Free', 'Free'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
        ('Lifetime', 'Lifetime'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='Free')
    max_devices = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
    
    def __str__(self):
        return f"{self.user.email} - {self.plan_type}"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        # Auto-update is_active based on expiry
        if self.expires_at and self.expires_at < timezone.now():
            self.is_active = False
        super().save(*args, **kwargs)


class Channel(models.Model):
    """
    Streaming channels
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(help_text="Private HLS/TS link")
    thumbnail = models.ImageField(upload_to='channels/', blank=True, null=True)
    is_live = models.BooleanField(default=False)
    viewers_count = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'channel'
        verbose_name = 'Channel'
        verbose_name_plural = 'Channels'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Sports events/matches
    """
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Live', 'Live'),
        ('Ended', 'Ended'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='events')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Upcoming')
    thumbnail = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event'
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['-start_time']
    
    def __str__(self):
        return self.title
    
    @property
    def is_live(self):
        now = timezone.now()
        return self.status == 'Live' and self.start_time <= now and (not self.end_time or now <= self.end_time)


class DeviceLimit(models.Model):
    """
    Track user devices for subscription limits
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='devices')
    device_identifier = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=50)  # mobile, desktop, tablet, tv
    last_used_at = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'device_limit'
        verbose_name = 'Device Limit'
        verbose_name_plural = 'Device Limits'
        unique_together = ['user', 'device_identifier']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name}"


class ReStreamTarget(models.Model):
    """
    Re-streaming targets (Telegram, Twitter, Facebook, etc.)
    """
    name = models.CharField(max_length=100)
    platform = models.CharField(max_length=50, help_text="Platform name (telegram, twitter, facebook, youtube)")
    rtmp_url = models.URLField(help_text="RTMP URL for streaming")
    stream_key = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 're_stream_target'
        verbose_name = 'Re-Stream Target'
        verbose_name_plural = 'Re-Stream Targets'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_rtmp_url(self):
        """Return complete RTMP URL with stream key"""
        if self.stream_key:
            return f"{self.rtmp_url}/{self.stream_key}"
        return self.rtmp_url


class ReStreamSession(models.Model):
    """
    Active re-streaming sessions
    """
    STATUS_CHOICES = [
        ('Starting', 'Starting'),
        ('Running', 'Running'),
        ('Stopped', 'Stopped'),
        ('Error', 'Error'),
    ]
    
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='restream_sessions')
    target = models.ForeignKey(ReStreamTarget, on_delete=models.CASCADE, related_name='sessions')
    source_url = models.URLField(help_text="Source M3U/HLS URL")
    rtmp_url = models.URLField(help_text="RTMP destination URL")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Starting')
    process_id = models.CharField(max_length=100, blank=True, null=True, help_text="FFmpeg process ID")
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    last_update = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 're_stream_session'
        verbose_name = 'Re-Stream Session'
        verbose_name_plural = 'Re-Stream Sessions'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.channel.name} -> {self.target.name}"
    
    @property
    def duration(self):
        """Calculate streaming duration"""
        if self.stopped_at:
            return self.stopped_at - self.started_at
        return timezone.now() - self.started_at