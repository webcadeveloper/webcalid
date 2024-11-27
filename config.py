"""Configuration file for port and host settings"""
import os
from typing import Dict, Any

# Default ports configuration with fixed values to prevent conflicts
PORT_CONFIG: Dict[str, int] = {
    'STREAMLIT': 8502,  # Main dashboard interface
    'API': 3000,        # REST API service
    'WEBRTC': 3001,     # WebRTC signaling
}

# Host configurations - Always use 0.0.0.0 for Replit deployment
HOST_CONFIG: Dict[str, str] = {
    'STREAMLIT': '0.0.0.0',
    'API': '0.0.0.0',
    'WEBRTC': '0.0.0.0',
}

# Environment variable getters with proper defaults
def get_port(service: str) -> int:
    """Get port number for a service with fallback to default"""
    env_var = f'{service}_PORT'
    return int(os.environ.get(env_var, PORT_CONFIG[service]))

def get_host(service: str) -> str:
    """Get host address for a service with fallback to default"""
    env_var = f'{service}_HOST'
    return os.environ.get(env_var, HOST_CONFIG[service])

def get_base_url(service: str) -> str:
    """Get base URL for a service with fallback to default"""
    env_var = f'{service}_BASE_URL'
    return os.environ.get(env_var, '')

# Exported configurations
STREAMLIT_PORT = get_port('STREAMLIT')
API_PORT = get_port('API')
WEBRTC_PORT = get_port('WEBRTC')

STREAMLIT_HOST = get_host('STREAMLIT')
API_HOST = get_host('API')
WEBRTC_HOST = get_host('WEBRTC')

STREAMLIT_BASE_URL = get_base_url('STREAMLIT')
API_BASE_URL = get_base_url('API')
WEBRTC_BASE_URL = get_base_url('WEBRTC')

# Session configuration
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour in seconds
