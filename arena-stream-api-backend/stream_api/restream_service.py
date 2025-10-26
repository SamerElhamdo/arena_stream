import subprocess
import os
from django.conf import settings
from .models import Channel, ReStreamTarget, ReStreamSession

def start_restream(source_url, rtmp_url, stream_key=None):
    """
    Start FFmpeg re-streaming from source to RTMP destination
    
    Args:
        source_url: M3U or HLS source URL
        rtmp_url: RTMP server URL
        stream_key: Optional stream key
    
    Returns:
        dict with process_id and status
    """
    try:
        # Construct RTMP URL
        if stream_key:
            full_rtmp = f"{rtmp_url}/{stream_key}"
        else:
            full_rtmp = rtmp_url
        
        # FFmpeg command for re-streaming
        # Using HLS input and RTMP output
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', source_url,
            '-c:v', 'copy',  # Copy video codec
            '-c:a', 'copy',  # Copy audio codec
            '-f', 'flv',
            '-stream_loop', '-1',  # Loop if stream ends
            '-reconnect', '1',  # Auto reconnect
            '-reconnect_at_eof', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '2',
            full_rtmp
        ]
        
        # Start FFmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        return {
            'process_id': str(process.pid),
            'status': 'Running',
            'error': None
        }
        
    except Exception as e:
        return {
            'process_id': None,
            'status': 'Error',
            'error': str(e)
        }


def stop_restream(process_id):
    """
    Stop FFmpeg process
    
    Args:
        process_id: Process ID to stop
    
    Returns:
        bool: Success status
    """
    try:
        # Kill process group
        os.killpg(int(process_id), 15)  # SIGTERM
        return True
    except Exception as e:
        try:
            # Force kill if SIGTERM didn't work
            os.killpg(int(process_id), 9)  # SIGKILL
            return True
        except:
            return False


def check_restream_status(process_id):
    """
    Check if FFmpeg process is still running
    
    Args:
        process_id: Process ID to check
    
    Returns:
        bool: True if running, False otherwise
    """
    try:
        os.kill(int(process_id), 0)  # Signal 0 doesn't kill, just checks
        return True
    except OSError:
        return False
