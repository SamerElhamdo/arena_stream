from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from . import views

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
    
    # Router URLs (for ViewSets)
    path('', include(router.urls)),
]
