import streamlit as st
from utils.phone_call import PhoneCallPage
from utils.auth_utils import check_authentication, check_role
from utils.phone_keypad import PhoneKeypad
from utils.webrtc import WebRTCHandler
from database import get_db_connection, add_phone_call, get_phone_calls
import json
import os

def page_render():
    # Check authentication
    if not st.session_state.get('user_id'):
        st.warning("Por favor inicie sesión")
        st.stop()
        return

    # Check if user has necessary permissions
    check_role('agent')
    
    # Initialize components
    phone_page = PhoneCallPage()
    keypad = PhoneKeypad()
    
    # Render phone call interface
    st.title("Sistema de Llamadas Telefónicas")
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Call controls
        st.subheader("Control de Llamadas")
        phone_page.render()
        
    with col2:
        # Keypad
        st.subheader("Teclado Numérico")
        keypad.render(phone_page._handle_keypad_input)
        
        # Volume control
        st.subheader("Control de Volumen")
        volume = st.slider("Volumen", 0, 100, 50)
        if volume != st.session_state.get('last_volume'):
            st.session_state.last_volume = volume
            phone_page.webrtc.set_volume(volume / 100)

if __name__ == "__main__":
    page_render()
