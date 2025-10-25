from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Subscription, Channel, Event, Category, DeviceLimit


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin interface for CustomUser
    """
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for Subscription
    """
    list_display = ('user', 'plan_type', 'max_devices', 'is_active', 'expires_at')
    list_filter = ('plan_type', 'is_active', 'starts_at', 'expires_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Plan Details', {'fields': ('plan_type', 'max_devices', 'price')}),
        ('Validity', {'fields': ('starts_at', 'expires_at', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category
    """
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """
    Admin interface for Channel
    """
    list_display = ('name', 'slug', 'category', 'is_live', 'viewers_count', 'created_at')
    list_filter = ('is_live', 'category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('viewers_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'description', 'category')}),
        ('Streaming', {'fields': ('source_url', 'thumbnail', 'is_live', 'viewers_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin interface for Event
    """
    list_display = ('title', 'channel', 'start_time', 'status', 'is_live')
    list_filter = ('status', 'channel', 'start_time', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('is_live', 'created_at', 'updated_at')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Event Info', {'fields': ('title', 'description', 'channel')}),
        ('Schedule', {'fields': ('start_time', 'end_time', 'status')}),
        ('Media', {'fields': ('thumbnail',)}),
        ('Status', {'fields': ('is_live',), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(DeviceLimit)
class DeviceLimitAdmin(admin.ModelAdmin):
    """
    Admin interface for DeviceLimit
    """
    list_display = ('user', 'device_name', 'device_type', 'is_blocked', 'last_used_at')
    list_filter = ('device_type', 'is_blocked', 'created_at')
    search_fields = ('user__email', 'device_name', 'device_identifier')
    readonly_fields = ('device_identifier', 'created_at', 'last_used_at')
    
    fieldsets = (
        ('User & Device', {'fields': ('user', 'device_identifier', 'device_name', 'device_type')}),
        ('Status', {'fields': ('is_blocked', 'last_used_at')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


# Customize admin site
admin.site.site_header = "ArenaStream Administration"
admin.site.site_title = "ArenaStream Admin"
admin.site.index_title = "Welcome to ArenaStream Administration"