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

    # Display active case information if available
    if 'current_case' in st.session_state:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT first_name, last_name, client_phone, other_client_phone
            FROM cases WHERE id = %s
        """, (st.session_state.current_case,))
        case_info = cur.fetchone()
        if case_info:
            st.info(f"Caso activo: {case_info[0]} {case_info[1]}")
            st.info(f"Teléfonos: {case_info[2]} / {case_info[3] or 'N/A'}")
        cur.close()
        conn.close()
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Call controls
        st.subheader("Control de Llamadas")
        phone_page.render()
        
        # Call history
        st.subheader("Historial de Llamadas")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.phone_number, c.call_status, c.call_duration, 
                   cs.first_name, cs.last_name
            FROM phone_calls c
            LEFT JOIN cases cs ON c.case_id = cs.id
            WHERE c.user_id = %s
            ORDER BY c.call_date DESC
            LIMIT 10
        """, (st.session_state.user_id,))
        calls = cur.fetchall()
        for call in calls:
            st.write(f"📞 {call[3]} {call[4]} - {call[0]} ({call[1]}) - {call[2]} segundos")
        cur.close()
        conn.close()
        
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
            
        # Call quality indicators
        st.subheader("Calidad de Llamada")
        if phone_page.webrtc.state == "connected":
            quality = phone_page.webrtc.get_call_quality()
            st.progress(quality['quality'] / 100, f"Calidad: {quality['quality']}%")
            st.metric("Latencia", f"{quality['latency']}ms")

if __name__ == "__main__":
    page_render()
