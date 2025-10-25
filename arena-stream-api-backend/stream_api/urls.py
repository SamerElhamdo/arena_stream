from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from . import views
from . import admin_views

# Create router for ViewSets (if any)
router = DefaultRouter()

app_name = 'stream_api'

urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='stream_api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='stream_api:schema'), name='redoc'),
    
    # Authentication
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Management
    path('user/me/', views.UserProfileView.as_view(), name='user-profile'),
    path('user/subscription/', views.SubscriptionView.as_view(), name='user-subscription'),
    path('user/devices/', views.DeviceListView.as_view(), name='user-devices'),
    
    # Channels
    path('channels/', views.ChannelListView.as_view(), name='channel-list'),
    path('channels/<int:pk>/', views.ChannelDetailView.as_view(), name='channel-detail'),
    path('channels/categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # Events
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/live/', views.LiveEventListView.as_view(), name='event-live'),
    path('events/upcoming/', views.UpcomingEventListView.as_view(), name='event-upcoming'),
    
    # Streaming
    path('stream/<int:pk>/play/', views.play_channel, name='stream-play'),
    path('stream/heartbeat/', views.heartbeat, name='stream-heartbeat'),
    path('stream/disconnect/', views.disconnect_stream, name='stream-disconnect'),
    
    # Admin Endpoints
    path('admin/users/', admin_views.AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', admin_views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/disable/', admin_views.disable_user, name='admin-disable-user'),
    path('admin/users/<int:user_id>/enable/', admin_views.enable_user, name='admin-enable-user'),
    
    path('admin/subscriptions/', admin_views.AdminSubscriptionListView.as_view(), name='admin-subscription-list'),
    path('admin/subscriptions/<int:pk>/', admin_views.AdminSubscriptionDetailView.as_view(), name='admin-subscription-detail'),
    
    path('admin/channels/', admin_views.AdminChannelListView.as_view(), name='admin-channel-list'),
    path('admin/channels/<int:pk>/', admin_views.AdminChannelDetailView.as_view(), name='admin-channel-detail'),
    
    path('admin/events/', admin_views.AdminEventListView.as_view(), name='admin-event-list'),
    path('admin/events/<int:pk>/', admin_views.AdminEventDetailView.as_view(), name='admin-event-detail'),
    
    path('admin/categories/', admin_views.AdminCategoryListView.as_view(), name='admin-category-list'),
    path('admin/categories/<int:pk>/', admin_views.AdminCategoryDetailView.as_view(), name='admin-category-detail'),
    
    path('admin/devices/', admin_views.AdminDeviceListView.as_view(), name='admin-device-list'),
    path('admin/devices/<int:pk>/', admin_views.AdminDeviceDetailView.as_view(), name='admin-device-detail'),
    
    path('admin/analytics/', admin_views.admin_analytics, name='admin-analytics'),
    path('admin/live-viewers/', admin_views.live_viewers, name='admin-live-viewers'),
    path('admin/disconnect-session/<int:user_id>/<str:session_id>/', admin_views.disconnect_user_session, name='admin-disconnect-session'),
    
    # Router URLs (for ViewSets)
    path('', include(router.urls)),
]
