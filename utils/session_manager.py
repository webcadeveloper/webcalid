import streamlit as st
from .number_search import number_search_page
from .phone_call import PhoneCallPage
from .supervisor_analytics import SupervisorAnalytics
from .i18n import I18nManager

def initialize_session_state():
    """Initialize and validate session state"""
    # Core session state initialization
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'generated_numbers' not in st.session_state:
        st.session_state.generated_numbers = []

    # Additional session state variables
    if 'language' not in st.session_state:
        st.session_state.language = 'es'
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = False

    # Pages state initialization
    if 'number_search' not in st.session_state:
        st.session_state.number_search = number_search_page
    if 'phone_call' not in st.session_state:
        st.session_state.phone_call = PhoneCallPage()
    if 'supervisor_analytics' not in st.session_state:
        st.session_state.supervisor_analytics = SupervisorAnalytics()
    if 'i18n' not in st.session_state:
        st.session_state.i18n = I18nManager()