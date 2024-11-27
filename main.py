import streamlit as st
import logging
import asyncio
import os
from database import init_db, get_user_by_username, update_user_profile, insert_case, get_cases_by_user
import nest_asyncio

# Initialize event loop before applying nest_asyncio
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
nest_asyncio.apply()

from auth import register_user, login_user, initiate_password_reset, reset_password, change_password
from utils.i18n import I18nManager
from utils.report_generator import ReportGenerator
from pages.number_generator import NumberGenerator
from pages.Case_Records_Management import CaseRecordsManagement
from scrapers.eoir_scraper import EOIRScraper
import time
import sys
import numpy as np
import pandas as pd
import matplotlib

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Initialize i18n
i18n = I18nManager()
_ = i18n.get_text

print("Python version:", sys.version)
print("Streamlit version:", st.__version__)
print("NumPy version:", np.__version__)
print("Pandas version:", pd.__version__)
print("Matplotlib version:", matplotlib.__version__)

class DashboardApp:
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()

    def setup_page_config(self):
        st.set_page_config(
            page_title="Sistema de Gestión de Casos",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': None,
                'Report a bug': None,
                'About': None
            }
        )
        # Ensure consistent port usage
        os.environ['STREAMLIT_SERVER_PORT'] = '8502'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        self.apply_custom_styles()
        self.load_js()

    def apply_custom_styles(self):
        theme = st.session_state.get('theme', 'light')
        
        # Define color schemes for different themes
        colors = {
            'light': {
                'bg': '#ffffff',
                'text': '#333333',
                'primary': '#2E3B55',
                'secondary': '#f0f2f6',
                'accent': '#4CAF50'
            },
            'dark': {
                'bg': '#1E1E1E',
                'text': '#E0E0E0',
                'primary': '#3E4E6E',
                'secondary': '#2D2D2D',
                'accent': '#5CBA5C'
            }
        }
        
        current_theme = colors[theme]
        
        st.markdown(f"""
        <style>
        /* Theme-based styles */
        .stApp {{
            background-color: {current_theme['bg']};
            color: {current_theme['text']};
        }}
        
        .number-display {{
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
            background-color: {current_theme['secondary']};
            color: {current_theme['text']};
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        
        .number-item {{
            padding: 5px;
            background-color: {current_theme['secondary']};
            color: {current_theme['text']};
            margin-bottom: 5px;
            border-radius: 3px;
        }}
        
        .profile-section {{
            background-color: {current_theme['secondary']};
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }}
        
        /* Custom form styling */
        .stTextInput > div > div {{
            background-color: {current_theme['bg']};
            color: {current_theme['text']};
        }}
        
        .stButton > button {{
            background-color: {current_theme['primary']} !important;
            color: white !important;
        }}
        
        .stButton > button:hover {{
            background-color: {current_theme['accent']} !important;
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {current_theme['primary']};
        }}
        </style>
        """, unsafe_allow_html=True)

    def load_js(self):
        st.markdown("""
        <script src="https://cdn.jsdelivr.net/npm/js-cookie@3.0.1/dist/js.cookie.min.js"></script>
        <script>
        function handleCookies() {
            const cookieManager = {
                setCookie: function(name, value, options = {}) {
                    const defaultOptions = {
                        path: '/',
                        sameSite: 'strict',
                        secure: location.protocol === 'https:'
                    };
                    const mergedOptions = {...defaultOptions, ...options};
                    try {
                        Cookies.set(name, value, mergedOptions);
                    } catch (error) {
                        console.error(`Error setting cookie ${name}:`, error);
                    }
                },
                getCookie: function(name) {
                    try {
                        return Cookies.get(name);
                    } catch (error) {
                        console.error(`Error getting cookie ${name}:`, error);
                        return null;
                    }
                },
                removeCookie: function(name) {
                    try {
                        Cookies.remove(name, { path: '/' });
                    } catch (error) {
                        console.error(`Error removing cookie ${name}:`, error);
                    }
                }
            };

            // Example usage (replace with your actual cookie logic)
            cookieManager.setCookie('__tld__', 'example_value');
        }

        // Run the function when the document is fully loaded
        document.addEventListener('DOMContentLoaded', handleCookies);
        </script>
        """, unsafe_allow_html=True)

    def initialize_session_state(self):
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
            
        # Application state initialization
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'number_generator' not in st.session_state:
            st.session_state.number_generator = NumberGenerator()
        if 'search_in_progress' not in st.session_state:
            st.session_state.search_in_progress = False
        if 'eoir_scraper' not in st.session_state:
            st.session_state.eoir_scraper = EOIRScraper()
            
        # Validate session consistency
        if st.session_state.user_id and not all([st.session_state.username, st.session_state.role]):
            logger.warning("Inconsistent session state detected, clearing session")
            st.session_state.clear()
            self.initialize_session_state()
            
        # Mark session as initialized
        st.session_state.session_initialized = True

    def render_login_form(self):
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.subheader("Iniciar Sesión")
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            col1, col2 = st.columns(2)
            with col1:
                remember_me = st.checkbox("Recordarme")
            with col2:
                st.markdown("[¿Olvidaste tu contraseña?](#forgot-password)", unsafe_allow_html=True)

            submitted = st.form_submit_button("Iniciar Sesión")
            if submitted:
                success, user = login_user(username, password)
                if success:
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.success("Inicio de sesión exitoso.")
                    st.rerun()
                else:
                    st.error("Nombre de usuario o contraseña incorrectos.")
        st.markdown("</div>", unsafe_allow_html=True)

    def render_register_form(self):
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        with st.form("register_form"):
            st.subheader("Registro de Usuario")

            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("Nombre")
            with col2:
                last_name = st.text_input("Apellido")

            username = st.text_input("Nombre de Usuario")
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Contraseña", type="password")

            role = st.selectbox(
                "Rol", 
                ["operator", "supervisor", "manager"],
                format_func=lambda x: {
                    "operator": "Operador",
                    "supervisor": "Supervisor",
                    "manager": "Manager"
                }[x]
            )

            terms = st.checkbox("Acepto los términos y condiciones")

            submitted = st.form_submit_button("Registrarse")
            if submitted:
                if password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                elif not terms:
                    st.error("Debe aceptar los términos y condiciones.")
                else:
                    success, message = register_user(username, password, email, first_name, last_name, role)
                    if success:
                        st.success(message)
                        st.info("Por favor, inicie sesión con sus nuevas credenciales.")
                    else:
                        st.error(message)
        st.markdown("</div>", unsafe_allow_html=True)

    def render_forgot_password_form(self):
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        with st.form("forgot_password_form"):
            st.subheader("Recuperar Contraseña")
            email = st.text_input("Correo Electrónico")
            submitted = st.form_submit_button("Enviar Correo de Recuperación")
            if submitted:
                success, message = initiate_password_reset(email)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        st.markdown("</div>", unsafe_allow_html=True)

    def render_reset_password_form(self):
        st.markdown("<div class='form-container'>", unsafe_allow_html=True)
        with st.form("reset_password_form"):
            st.subheader("Restablecer Contraseña")
            token = st.text_input("Token de Restablecimiento")
            new_password = st.text_input("Nueva Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
            submitted = st.form_submit_button("Restablecer Contraseña")
            if submitted:
                if new_password != confirm_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    success, message = reset_password(token, new_password)
                    if success:
                        st.success(message)
                        st.info("Por favor, inicie sesión con su nueva contraseña.")
                    else:
                        st.error(message)
        st.markdown("</div>", unsafe_allow_html=True)

    def render_change_password_form(self):
        with st.form("change_password_form"):
            st.subheader("Cambiar Contraseña")
            current_password = st.text_input("Contraseña Actual", type="password")
            new_password = st.text_input("Nueva Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
            submitted = st.form_submit_button("Cambiar Contraseña")
            if submitted:
                if new_password != confirm_password:
                    st.error("Las nuevas contraseñas no coinciden.")
                else:
                    success, message = change_password(st.session_state.user_id, current_password, new_password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    def render_profile_editor(self):
        if not st.session_state.user_id:
            return

        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
        st.subheader("Editar Perfil")

        user = get_user_by_username(st.session_state.username)

        if user:
            # Información Personal
            st.markdown("### Información Personal")
            col1, col2 = st.columns(2)
            with col1:
                new_first_name = st.text_input("Nombre", value=user['first_name'] or "")
                new_email = st.text_input("Email", value=user['email'] or "")
                new_phone = st.text_input("Teléfono", value=user.get('phone', ''))
            with col2:
                new_last_name = st.text_input("Apellido", value=user['last_name'] or "")
                new_address = st.text_area("Dirección", value=user.get('address', ''), height=100)
            
            # Preferencias
            st.markdown("### Preferencias")
            new_theme = st.selectbox(
                "Tema",
                options=['light', 'dark'],
                index=0 if user.get('theme_preference', 'light') == 'light' else 1
            )

            if st.button("Actualizar Perfil"):
                updates = {}
                if new_first_name != user['first_name']:
                    updates['first_name'] = new_first_name
                if new_last_name != user['last_name']:
                    updates['last_name'] = new_last_name
                if new_email != user['email']:
                    updates['email'] = new_email
                if new_phone != user.get('phone'):
                    updates['phone'] = new_phone
                if new_address != user.get('address'):
                    updates['address'] = new_address
                if new_theme != user.get('theme_preference'):
                    updates['theme_preference'] = new_theme
                    if 'theme' not in st.session_state:
                        st.session_state.theme = new_theme

                if updates:
                    try:
                        update_user_profile(st.session_state.user_id, updates)
                        st.success("Perfil actualizado correctamente")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error al actualizar perfil: {e}")
                        st.error("Ocurrió un error al actualizar el perfil. Por favor, inténtalo de nuevo más tarde.")

            st.markdown("### Información de la Cuenta")
            st.write(f"**Usuario:** {user['username']}")
            st.write(f"**Rol:** {user['role']}")
            st.write(f"**Fecha de Registro:** {user['created_at']}")

            if st.button("Cambiar Contraseña"):
                self.render_change_password_form()

        st.markdown("</div>", unsafe_allow_html=True)

    def run(self):
        print("Starting main function")
        try:
            number_generator = NumberGenerator()
            case_records = CaseRecordsManagement()

            st.sidebar.title("Navigation")
            page = st.sidebar.radio("Go to", ["Dashboard", "Number Generator", "Case Records"])

            if page == "Dashboard":
                self.render_main_page()
            elif page == "Number Generator":
                number_generator.run()
            elif page == "Case Records":
                case_records.run()

        except Exception as e:
            print(f"Error in main function: {e}")
            st.error(f"An error occurred: {e}")
            raise

    def render_main_page(self):
        st.title(f"Bienvenido, {st.session_state.username}")

        # Sidebar for user actions
        with st.sidebar:
            st.subheader("Acciones de Usuario")
            
            # Theme selector
            theme_options = {
                'light': '☀️ Claro',
                'dark': '🌙 Oscuro'
            }
            current_theme = st.session_state.get('theme', 'light')
            new_theme = st.selectbox(
                "Tema",
                options=list(theme_options.keys()),
                format_func=lambda x: theme_options[x],
                index=0 if current_theme == 'light' else 1,
                key="theme_selector"
            )
            
            if new_theme != current_theme:
                st.session_state.theme = new_theme
                st.rerun()
            
            # User actions
            if st.button("✏️ Editar Perfil", type="primary"):
                self.render_profile_editor()
            if st.button("📊 Generar Reporte", type="secondary"):
                self.render_report()
            if st.button("🚪 Cerrar Sesión", type="secondary"):
                st.session_state.clear()
                st.rerun()

        # Main content
        st.header("Generador de Números y Registro de Casos")

        # Mostrar los números generados previamente
        current_number = st.session_state.generated_numbers[-1] if st.session_state.generated_numbers else "000000000"
        st.markdown(f'<div class="number-display">{current_number}</div>', unsafe_allow_html=True)

        # Botón para generar nuevos números
        if st.button("Generar Nuevo Número"):
            new_number = st.session_state.number_generator.generate_number()
            st.session_state.generated_numbers.append(new_number)
            st.success(f"Nuevo número generado: {new_number}")

        col1, col2 = st.columns(2)

        report_placeholder = st.empty()

        with col1:
            if st.button("Iniciar Búsqueda Automática"):
                st.session_state.search_in_progress = True

        with col2:
            if st.button("Detener Búsqueda"):
                st.session_state.search_in_progress = False

        st.subheader("Buscar número específico")
        specific_number = st.text_input("Ingrese el número a buscar:")
        if st.button("Buscar"):
            if specific_number:
                search_result = self.search_number(specific_number, report_placeholder)
                st.session_state.search_history.append(search_result)
            else:
                st.error("Por favor, ingrese un número para buscar.")

        if st.session_state.search_in_progress:
            while st.session_state.search_in_progress:
                new_number = st.session_state.number_generator.generate_number()
                st.session_state.generated_numbers.append(new_number)
                search_result = self.search_number(new_number, report_placeholder)
                st.session_state.search_history.append(search_result)

                if search_result['eoir_found']:
                    st.session_state.search_in_progress = False
                    break

                time.sleep(1)

        self.render_search_history()

        # Agregar Iframe de EOIR
        st.subheader("Página EOIR")
        st.markdown('<iframe src="https://acis.eoir.justice.gov/en/" width="100%" height="500px"></iframe>', unsafe_allow_html=True)

        # Mostrar formulario de registro
        self.render_form()

    def render_form(self):
        st.subheader("Formulario de Registro de Caso")

        # Campos obligatorios
        st.markdown("### Campos Obligatorios")
        case_number = st.text_input("Número de caso *")
        case_status = st.selectbox("Estado del caso *", ["Positivo", "Negativo"])
        first_name = st.text_input("Nombre *")
        last_name = st.text_input("Apellido *")
        a_number = st.text_input("A-number (9 dígitos) *")
        court_address = st.text_input("Dirección de la Corte *")
        court_phone = st.text_input("Teléfono de la Corte *")

        # Campos opcionales
        st.markdown("### Campos Opcionales")
        client_phone = st.text_input("Teléfono del Cliente")
        other_client_phone = st.text_input("Otro teléfono del Cliente")
        client_address = st.text_input("Dirección del Cliente")
        client_email = st.text_input("Email del Cliente")

        if st.button("Guardar Caso"):
            # Verificar solo los campos obligatorios
            if all([case_number, case_status, first_name, last_name, 
                    a_number, court_address, court_phone]):

                # Validar formato del A-number
                if len(a_number) != 9 or not a_number.isdigit():
                    st.error("El A-number debe contener exactamente 9 dígitos")
                    return

                if insert_case({
                    'number': case_number,
                    'status': case_status,
                    'is_positive': case_status == "Positivo",
                    'first_name': first_name,
                    'last_name': last_name,
                    'a_number': a_number,
                    'court_address': court_address,
                    'court_phone': court_phone,
                    'client_phone': client_phone,
                    'other_client_phone': other_client_phone,
                    'client_address': client_address,
                    'client_email': client_email,
                    'created_by': st.session_state.user_id
                }):
                    st.success(f"El caso {case_number} ha sido guardado con éxito.")
            else:
                st.error("Por favor, complete todos los campos obligatorios (marcados con *)")

    def search_number(self, number, report_placeholder):
        report_placeholder.info(f"Buscando número: {number}")

        eoir_result = st.session_state.eoir_scraper.search(number)

        if eoir_result['status'] == 'success':
            report_placeholder.success("¡Caso encontrado en EOIR!")
            case_status = eoir_result['data']['status'].lower()
            is_positive = "positivo" in case_status or "en proceso" in case_status
            return {'number': number, 'eoir_found': True, 'is_positive': is_positive, 'eoir_data': eoir_result['data']}
        elif eoir_result['status'] == 'not_found':
            report_placeholder.info("No se encontró el caso en EOIR")
            return {'number': number, 'eoir_found': False, 'is_positive': False}
        else:
            report_placeholder.error(f"Error al buscar en EOIR: {eoir_result.get('error', 'Error desconocido')}")
            return {'number': number, 'eoir_found': False, 'is_positive': False}

    def render_search_history(self):
        if st.session_state.search_history:
            st.markdown("<h3>Historial de Búsquedas</h3>", unsafe_allow_html=True)
            for item in reversed(st.session_state.search_history):
                status_text = "Positivo" if item.get('is_positive') else "Negativo"
                st.markdown(f"<div class='number-item'>{item['number']} - {status_text}</div>", unsafe_allow_html=True)

    def render_report(self):
        st.subheader("Generar Reporte")

        # Obtener todos los casos del usuario actual
        cases = get_cases_by_user(st.session_state.user_id)

        if not cases:
            st.warning("No hay casos registrados para generar un reporte.")
            return

        report_generator = ReportGenerator(cases)
        report_generator.generate_report()

def main():
    print("Starting script")
    app = DashboardApp()
    app.run()

if __name__ == "__main__":
    main()

