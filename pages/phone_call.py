import streamlit as st
from webrtc import WebRTCHandler
from database import add_phone_call, get_db_connection
import json

class PhoneCallPage:
    def __init__(self):
        self.webrtc = WebRTCHandler()

    def render(self):
        st.title("Sistema de Llamadas")

        # Panel de control de llamada
        col1, col2 = st.columns(2)

        with col1:
            number = st.text_input("Número a llamar")
            if st.button("Iniciar Llamada", type="primary"):
                call_id = self._start_call(number)
                st.session_state.current_call = call_id

            if st.button("Finalizar Llamada", type="secondary"):
                self._end_call()

        with col2:
            volume = st.slider("Volumen", 0, 100, 50)
            is_muted = st.checkbox("Silenciar micrófono")

            self.webrtc.set_volume(volume)
            self.webrtc.set_mute(is_muted)

        # Historial de llamadas
        self._show_call_history()

    def _start_call(self, number):
        conn = get_db_connection()
        try:
            call_id = add_phone_call(
                search_id=st.session_state.current_search,
                phone_number=number,
                status="iniciada"
            )
            self.webrtc.start_call(number)
            return call_id
        finally:
            conn.close()

    def _end_call(self):
        if hasattr(st.session_state, 'current_call'):
            conn = get_db_connection()
            try:
                duration = self.webrtc.get_call_duration()
                add_phone_call(
                    st.session_state.current_call,
                    status="finalizada",
                    duration=duration
                )
            finally:
                conn.close()
            self.webrtc.end_call()

    def _show_call_history(self):
        st.subheader("Historial de Llamadas")
        calls = self._get_call_history()

        for call in calls:
            with st.expander(f"Llamada {call['id']} - {call['phone_number']}"):
                st.write(f"Estado: {call['status']}")
                st.write(f"Duración: {call['duration']} segundos")
                st.write(f"Notas: {call['notes']}")