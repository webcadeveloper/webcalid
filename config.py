"""Configuration file for port and host settings"""
import os

# Default ports
STREAMLIT_PORT = int(os.environ.get('STREAMLIT_PORT', 8502))
API_PORT = int(os.environ.get('API_PORT', 3000))
WEBRTC_PORT = int(os.environ.get('WEBRTC_PORT', 3001))

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
