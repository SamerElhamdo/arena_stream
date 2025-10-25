"""
URL configuration for arena_core project.

ArenaStream - Sports Streaming Platform Backend API
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('stream_api.urls')),
]
