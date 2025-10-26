from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
import json

from .models import ReStreamTarget, ReStreamSession, Channel
from .serializers import (
    ReStreamTargetSerializer, ReStreamSessionSerializer, 
    ReStreamStartSerializer
)
from .restream_service import start_restream, stop_restream, check_restream_status


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


# Re-Stream Target Management
class ReStreamTargetListView(generics.ListCreateAPIView):
    """
    List/Create re-stream targets (Admin only)
    """
    queryset = ReStreamTarget.objects.all()
    serializer_class = ReStreamTargetSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class ReStreamTargetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific re-stream target (Admin only)
    """
    queryset = ReStreamTarget.objects.all()
    serializer_class = ReStreamTargetSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


# Re-Stream Session Management
class ReStreamSessionListView(generics.ListAPIView):
    """
    List all re-streaming sessions (Admin only)
    """
    queryset = ReStreamSession.objects.all()
    serializer_class = ReStreamSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', None)
        queryset = ReStreamSession.objects.all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-started_at')


class ReStreamSessionDetailView(generics.RetrieveDestroyAPIView):
    """
    Get/Delete specific re-streaming session (Admin only)
    """
    queryset = ReStreamSession.objects.all()
    serializer_class = ReStreamSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def start_restream_session(request):
    """
    Start a new re-streaming session (Admin only)
    """
    from .serializers import ReStreamStartSerializer
    
    serializer = ReStreamStartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        channel = Channel.objects.get(id=serializer.validated_data['channel_id'])
        target = ReStreamTarget.objects.get(id=serializer.validated_data['target_id'])
        source_url = serializer.validated_data['source_url']
        
        # Start FFmpeg re-streaming
        result = start_restream(
            source_url=source_url,
            rtmp_url=target.rtmp_url,
            stream_key=target.stream_key
        )
        
        # Create session record
        session = ReStreamSession.objects.create(
            channel=channel,
            target=target,
            source_url=source_url,
            rtmp_url=target.full_rtmp_url,
            status=result['status'],
            process_id=result['process_id'],
            error_message=result.get('error')
        )
        
        session_serializer = ReStreamSessionSerializer(session)
        
        return Response({
            'message': 'Re-streaming session started successfully',
            'session': session_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def stop_restream_session(request, session_id):
    """
    Stop a re-streaming session (Admin only)
    """
    try:
        session = ReStreamSession.objects.get(id=session_id)
        
        if session.process_id:
            success = stop_restream(session.process_id)
            
            if success:
                session.status = 'Stopped'
                session.stopped_at = timezone.now()
                session.save()
                
                return Response({
                    'message': 'Re-streaming session stopped successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to stop the stream'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'error': 'No active process to stop'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except ReStreamSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def get_restream_status(request, session_id):
    """
    Get re-streaming session status (Admin only)
    """
    try:
        session = ReStreamSession.objects.get(id=session_id)
        
        # Check if FFmpeg process is still running
        if session.process_id:
            is_running = check_restream_status(session.process_id)
            
            if not is_running and session.status == 'Running':
                # Process died unexpectedly
                session.status = 'Error'
                session.error_message = 'FFmpeg process terminated unexpectedly'
                session.stopped_at = timezone.now()
                session.save()
        
        serializer = ReStreamSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except ReStreamSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminUser])
def list_active_restreams(request):
    """
    Get all active re-streaming sessions (Admin only)
    """
    try:
        # Get all running sessions
        running_sessions = ReStreamSession.objects.filter(status='Running')
        
        # Check each session
        for session in running_sessions:
            if session.process_id:
                is_running = check_restream_status(session.process_id)
                if not is_running:
                    session.status = 'Error'
                    session.error_message = 'Process terminated unexpectedly'
                    session.stopped_at = timezone.now()
                    session.save()
        
        # Get updated list
        all_sessions = ReStreamSession.objects.all()
        serializer = ReStreamSessionSerializer(all_sessions, many=True)
        
        return Response({
            'count': all_sessions.count(),
            'active': all_sessions.filter(status='Running').count(),
            'sessions': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
