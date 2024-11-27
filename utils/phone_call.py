import streamlit as st
import threading
import time
from utils.webrtc import WebRTCHandler
from utils.usb_manager import USBManager
from utils.database import add_phone_call, get_phone_calls, add_verification_form, get_verification_forms

class PhoneCallPage:
    def __init__(self):
        self.webrtc = WebRTCHandler()
        self.usb_manager = USBManager()
        self.current_call = None
        self.call_duration = 0
        self.call_start_time = None

    def render(self):
        st.title("Llamadas Telefónicas")

        if 'call_history' not in st.session_state:
            st.session_state.call_history = []

        self._render_call_controls()
        self._render_call_history()
        self._render_verification_forms()
        self._render_usb_controls()

    def _render_call_controls(self):
        st.header("Controles de Llamada")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Iniciar Llamada"):
                self._start_call()

        with col2:
            if st.button("Poner en Espera"):
                self._hold_call()

        with col3:
            if st.button("Reanudar Llamada"):
                self._resume_call()

        with col4:
            if st.button("Finalizar Llamada"):
                self._end_call()

        if self.current_call:
            st.write(f"Llamada en curso con el número: {self.current_call['phone_number']}")
            self._render_call_controls_during_call()

    def _render_call_controls_during_call(self):
        st.header("Controles de Llamada Activa")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            volume = st.slider("Volumen", 0, 100, 50)
            self.webrtc.set_volume(volume / 100)

        with col2:
            if st.button("Agregar Nota"):
                self._add_call_note()

        with col3:
            if st.button("Generar Formulario de Verificación"):
                self._generate_verification_form()

        with col4:
            if st.button("Finalizar Llamada"):
                self._end_call()

    def _start_call(self):
        if not st.session_state.get('current_case'):
            st.error("No hay caso seleccionado para llamar")
            return
            
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT client_phone, other_client_phone, first_name, last_name
                FROM cases WHERE id = %s
            """, (st.session_state.current_case,))
            case_info = cur.fetchone()
            
            if not case_info or not case_info[0]:
                st.error("No hay número de teléfono disponible para este caso")
                return
                
            phone_number = st.session_state.get('current_phone', case_info[0])
            success = self.webrtc.start_call(phone_number)
            
            if success:
                self.current_call = {
                    'phone_number': phone_number,
                    'status': 'initiated',
                    'duration': 0,
                    'notes': None,
                    'case_id': st.session_state.current_case
                }
                
                call_id = add_phone_call(
                    user_id=st.session_state.user_id,
                    phone_number=phone_number,
                    status='initiated',
                    duration=0,
                    notes=None,
                    case_id=st.session_state.current_case
                )
                
                self.current_call['id'] = call_id
                self.call_start_time = time.time()
                st.success(f"Llamando a {case_info[2]} {case_info[3]} - {phone_number}")
                self._update_call_duration()
                
        except Exception as e:
            st.error(f"Error al iniciar la llamada: {str(e)}")
        finally:
            cur.close()
            conn.close()

    def _hold_call(self):
        if self.current_call:
            self.current_call['status'] = 'on_hold'
            self.webrtc.hold_call()
            self._update_call_duration()
        else:
            st.error("No active call to put on hold")

    def _resume_call(self):
        if not self.current_call:
            st.error("No hay una llamada activa para reanudar")
            return
            
        self.current_call['status'] = 'in_progress'
        self.webrtc.resume_call()
        self.call_start_time = time.time()
        self._update_call_duration()

    def _end_call(self):
        if not self.current_call:
            return
            
        self.current_call['status'] = 'ended'
        self.current_call['duration'] = self.call_duration
        self.webrtc.end_call()
        self.current_call = None
        self.call_duration = 0
        self.call_start_time = None

    def _add_call_note(self):
        if not self.current_call:
            st.error("No hay una llamada activa para agregar notas")
            return
            
        note = st.text_input("Agregar nota a la llamada")
        if note and st.button("Guardar Nota"):
            self.current_call['notes'] = note
            add_phone_call(
                st.session_state.user_id,
                self.current_call['phone_number'],
                self.current_call['status'],
                self.current_call['duration'],
                self.current_call['notes']
            )

    def _generate_verification_form(self):
        if not self.current_call:
            st.error("No hay una llamada activa para generar el formulario")
            return
            
        form_data = {
            'customer_name': st.text_input("Nombre del cliente"),
            'customer_address': st.text_input("Dirección del cliente"),
            'customer_phone': st.text_input("Teléfono del cliente"),
            'verification_notes': st.text_area("Notas de verificación")
        }
        if st.button("Enviar Formulario de Verificación"):
            add_verification_form(
                st.session_state.user_id,
                self.current_call['phone_number'],
                form_data,
                "submitted",
                self.current_call.get('notes')
            )
            st.success("Formulario de verificación enviado")

    def _render_call_history(self):
        st.header("Historial de Llamadas")

        if st.session_state.call_history:
            for call in reversed(st.session_state.call_history):
                st.write(f"Número: {call['phone_number']} - Estado: {call['status']} - Duración: {call['duration']} segundos")
        else:
            st.write("No hay llamadas en el historial.")

    def _render_verification_forms(self):
        st.header("Formularios de Verificación")

        if st.session_state.call_history:
            for call in reversed(st.session_state.call_history):
                verification_forms = get_verification_forms(call['id'])
                if verification_forms:
                    for form in verification_forms:
                        st.write(f"Número: {form['phone_number']} - Estado: {form['status']} - Notas: {form['notes']}")
                        st.json(form['form_data'])
        else:
            st.write("No hay formularios de verificación.")

    def _render_usb_controls(self):
        st.header("Administración de Hardware USB")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Conectar Dispositivo USB"):
                self.usb_manager.connect_device()

        with col2:
            if st.button("Desconectar Dispositivo USB"):
                self.usb_manager.disconnect_device()

        with col3:
            selected_device = st.selectbox("Seleccionar Dispositivo", self.usb_manager.get_connected_devices())
            if st.button(f"Configurar {selected_device}"):
                self.usb_manager.configure_device(selected_device)

    def _update_call_duration(self):
        while self.current_call and self.current_call['status'] in ['in_progress', 'on_hold']:
            if self.call_start_time is not None:
                self.call_duration = int(time.time() - self.call_start_time)
                st.session_state.experimental_rerun()
            time.sleep(1)