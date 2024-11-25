import streamlit as st
from utils.webrtc import WebRTCHandler
from database import add_phone_call, get_db_connection, get_phone_calls
from utils.phone_keypad import PhoneKeypad
import json
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime
import os

class PhoneCallPage:
    def __init__(self):
        self.webrtc = WebRTCHandler()
        self.initialize_session_state()

    def initialize_session_state(self):
        if 'current_call' not in st.session_state:
            st.session_state.current_call = None
        if 'recording' not in st.session_state:
            st.session_state.recording = False
        if 'call_notes' not in st.session_state:
            st.session_state.call_notes = ""

    def render(self):
        st.title("Sistema de Llamadas")
        
        # Main call controls
        self._render_call_controls()
        
        # Call features
        if st.session_state.current_call:
            self._render_active_call_features()
        
        # Call history
        self._show_call_history()

    def _render_call_controls(self):
        col1, col2 = st.columns(2)

        with col1:
            if not st.session_state.current_call:
                number = st.text_input("Número a llamar", key="call_number")
                if st.button("Iniciar Llamada", type="primary"):
                    self._start_call(number)
            else:
                st.error("Llamada en curso")
                if st.button("Finalizar Llamada", type="secondary"):
                    self._end_call()

        with col2:
            volume = st.slider("Volumen", 0, 100, 50, key="call_volume")
            is_muted = st.checkbox("Silenciar micrófono", key="call_mute")
            
            if st.session_state.current_call:
                self.webrtc.set_volume(volume)
                self.webrtc.set_mute(is_muted)

    def _render_active_call_features(self):
        st.subheader("Características de la llamada activa")
        
        # Recording controls
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state.recording:
                if st.button("Iniciar Grabación"):
                    self._start_recording()
            else:
                if st.button("Detener Grabación"):
                    self._stop_recording()
                
        with col2:
            # Call notes
            st.text_area(
                "Notas de la llamada",
                value=st.session_state.call_notes,
                key="current_call_notes",
                on_change=self._update_call_notes
            )

    def _start_call(self, number):
        try:
            # Verify SSID and CallCentric configuration
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT ssid, sip_username, sip_password 
                FROM users 
                WHERE id = %s
            """, (st.session_state.get('user_id'),))
            user_config = cur.fetchone()
            
            if not user_config or not user_config[0]:
                st.error("Error: Es necesario configurar el SSID en su perfil antes de realizar llamadas.")
                st.info("Por favor, vaya a su perfil y configure el SSID proporcionado por Central Centric.")
                return
                
            if not user_config[1] or not user_config[2]:
                st.error("Error: Es necesario configurar las credenciales de CallCentric antes de realizar llamadas.")
                st.info("Por favor, vaya a su perfil y configure sus credenciales de CallCentric.")
                return
            
            # Initialize WebRTC connection
            if self.webrtc.start_call(number):
                try:
                    call_id = add_phone_call(
                        search_id=st.session_state.get('current_search'),
                        user_id=st.session_state.get('user_id'),
                        phone_number=number,
                        status="iniciada"
                    )
                    st.session_state.current_call = {
                        'id': call_id,
                        'number': number,
                        'start_time': datetime.now()
                    }
                    st.success(f"Llamada iniciada con {number}")
                finally:
                    cur.close()
            else:
                st.error("Error al iniciar la llamada")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            conn.close()

    def _end_call(self):
        if st.session_state.current_call:
            try:
                # Stop recording if active
                if st.session_state.recording:
                    self._stop_recording()
                
                # Calculate call duration
                duration = (datetime.now() - st.session_state.current_call['start_time']).seconds
                
                # Update call record
                conn = get_db_connection()
                try:
                    add_phone_call(
                        user_id=st.session_state.get('user_id'),
                        phone_number=st.session_state.current_call['number'],
                        status="finalizada",
                        duration=duration,
                        notes=st.session_state.call_notes
                    )
                finally:
                    conn.close()
                
                # Clean up WebRTC
                self.webrtc.end_call()
                
                # Reset session state
                st.session_state.current_call = None
                st.session_state.recording = False
                st.session_state.call_notes = ""
                
                st.success("Llamada finalizada")
            except Exception as e:
                st.error(f"Error al finalizar la llamada: {str(e)}")

    def _start_recording(self):
        if st.session_state.current_call:
            try:
                self.webrtc.start_recording()
                st.session_state.recording = True
                st.success("Grabación iniciada")
            except Exception as e:
                st.error(f"Error al iniciar la grabación: {str(e)}")

    def _stop_recording(self):
        if st.session_state.recording:
            try:
                recording_path = self.webrtc.stop_recording()
                st.session_state.recording = False
                st.success("Grabación guardada")
                
                # Update call record with recording path
                conn = get_db_connection()
                try:
                    add_phone_call(
                        user_id=st.session_state.get('user_id'),
                        phone_number=st.session_state.current_call['number'],
                        status=st.session_state.current_call.get('status', 'recording'),
                        duration=st.session_state.current_call.get('duration', 0),
                        notes=st.session_state.call_notes,
                        recording_url=recording_path
                    )
                finally:
                    conn.close()
            except Exception as e:
                st.error(f"Error al detener la grabación: {str(e)}")

    def _update_call_notes(self):
        st.session_state.call_notes = st.session_state.current_call_notes

    def _show_call_history(self):
        st.subheader("Historial de Llamadas")
        
        try:
            conn = get_db_connection()
            calls = get_phone_calls(user_id=st.session_state.get('user_id'))
            
            if not calls:
                st.info("No hay llamadas en el historial")
                return
                
            for call in calls:
                with st.expander(f"Llamada {call['id']} - {call['phone_number']}"):
                    st.write(f"Estado: {call['call_status']}")
                    st.write(f"Duración: {call['duration']} segundos")
                    
                    if call['notes']:
                        st.write(f"Notas: {call['notes']}")
                        
                    if call['recording_url']:
                        st.audio(call['recording_url'])
                        
        except Exception as e:
            st.error(f"Error al cargar el historial: {str(e)}")