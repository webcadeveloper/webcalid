import streamlit as st
import logging
import os
import asyncio
import sys
from pathlib import Path
from event_loop_setup import setup_event_loop
from utils.session_manager import initialize_session_state
from utils.auth_middleware import AuthMiddleware
from utils.auth_utils import check_role
from utils.i18n import I18nManager
from pages.dashboard import DashboardApp
from components.auth import render_login_form, render_register_form
from database import init_db
from config import (
    STREAMLIT_PORT,
    STREAMLIT_HOST,
    STREAMLIT_BASE_URL,
    API_PORT,
    API_HOST,
    WEBRTC_PORT,
    WEBRTC_HOST
)
import requests

# Configure logging with enhanced format and file output
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "main.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Verificar si las variables de entorno necesarias están configuradas
def verify_environment():
    required_vars = {
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'STREAMLIT_PORT': STREAMLIT_PORT,
        'API_PORT': API_PORT,
        'WEBRTC_PORT': WEBRTC_PORT
    }
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.info("Environment verification completed successfully")
    return True

# Configuración de variables de entorno
def configure_environment():
    try:
        os.environ['STREAMLIT_SERVER_PORT'] = str(STREAMLIT_PORT)
        os.environ['STREAMLIT_SERVER_ADDRESS'] = STREAMLIT_HOST
        os.environ['STREAMLIT_SERVER_BASE_URL'] = STREAMLIT_BASE_URL
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

        os.environ['API_SERVER_HOST'] = f"http://{API_HOST}:{API_PORT}"
        os.environ['WEBRTC_SERVER_HOST'] = f"ws://{WEBRTC_HOST}:{WEBRTC_PORT}"
        logger.info("Environment configuration completed successfully")
    except Exception as e:
        logger.error(f"Error configuring environment: {str(e)}")
        raise

# Inicialización de servicios
async def initialize_services():
    try:
        await asyncio.to_thread(init_db)
        logger.info("Database initialization completed")
        initialize_session_state()
        logger.info("Session state initialized")
        I18nManager()  # Initialize i18n manager
        logger.info("I18n manager initialized")
        return True
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        raise

# Crear un nuevo caso usando la API
def create_case(name, description):
    api_url = f"http://{API_HOST}:{API_PORT}/api/cases"
    data = {"name": name, "description": description}
    try:
        response = requests.post(api_url, json=data)
        if response.status_code == 200:
            st.success("Caso creado con éxito!")
        else:
            st.error(f"Error al crear el caso: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la conexión con la API: {e}")

# Configuración de la página de Streamlit
def configure_page():
    st.set_page_config(
        page_title="Sistema de Gestión de Casos",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
    )

# Renderizar la página de error con detalles
def render_error_page(error_msg):
    st.error("Ha ocurrido un error")
    st.write(error_msg)
    if st.button("Reiniciar aplicación"):
        st.session_state.clear()
        st.experimental_rerun()

# Manejo de la autenticación y verificación de roles
async def handle_auth_middleware():
    try:
        auth = AuthMiddleware()
        is_auth = await auth.is_authenticated()
        if not is_auth:
            logger.warning("Usuario no autenticado, redirigiendo a página de login")
            render_auth_page()
            return False
        logger.info("Usuario autenticado correctamente")
        return True
    except Exception as e:
        logger.error(f"Error en middleware de autenticación: {str(e)}")
        st.error("Error en la autenticación. Por favor, intente nuevamente.")
        return False

# Renderizar la página de autenticación
def render_auth_page():
    st.title("Sistema de Gestión de Casos")
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    with tab1:
        render_login_form()
    with tab2:
        render_register_form()

# Renderizar la página de gestión de casos
def render_dashboard():
    st.title("Gestión de Casos")

    case_name = st.text_input("Nombre del caso")
    case_description = st.text_area("Descripción del caso")

    if st.button("Crear caso"):
        if case_name and case_description:
            create_case(case_name, case_description)
        else:
            st.error("Por favor, complete todos los campos.")

# Función principal para la ejecución de la aplicación
async def main():
    try:
        # Inicialización de la sesión de usuario
        if not st.session_state.get('_session_initialized'):
            initialize_session_state()
            st.session_state['_session_initialized'] = True
            logger.info("Session state initialized successfully")

        # Verificación y configuración del entorno
        verify_environment()
        configure_environment()
        logger.info("Environment configured successfully")

        # Configuración de la página de Streamlit
        configure_page()
        logger.info("Page configuration completed")

        # Inicialización de servicios
        await initialize_services()
        logger.info("Services initialized successfully")

        # Manejo de la autenticación
        if not await handle_auth_middleware():
            return

        # Renderización del dashboard
        render_dashboard()

    except Exception as e:
        logger.critical(f"Critical application error: {str(e)}", exc_info=True)
        render_error_page("Error crítico en la aplicación. Por favor, contacte al administrador.")

if __name__ == "__main__":
    try:
        logger.info("Iniciando aplicación...")
        asyncio.run(main())
        logger.info("Aplicación iniciada correctamente")
    except Exception as e:
        logger.critical(f"Error fatal en la aplicación: {str(e)}")
