"""Configuration file for port and host settings"""
import os

# Default ports with fixed values to prevent conflicts
STREAMLIT_PORT = 8502  # Fixed Streamlit port
API_PORT = 3000       # Fixed API port
WEBRTC_PORT = 3001    # Fixed WebRTC port

# Host configurations
STREAMLIT_HOST = os.environ.get('STREAMLIT_HOST', '0.0.0.0')
API_HOST = os.environ.get('API_HOST', '0.0.0.0')
WEBRTC_HOST = os.environ.get('WEBRTC_HOST', '0.0.0.0')

# Base URLs
STREAMLIT_BASE_URL = os.environ.get('STREAMLIT_BASE_URL', '')
API_BASE_URL = os.environ.get('API_BASE_URL', '')
WEBRTC_BASE_URL = os.environ.get('WEBRTC_BASE_URL', '')

# Session configuration
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour in seconds
