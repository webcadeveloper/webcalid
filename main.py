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

def verify_environment():
    """Verify all required environment variables and configurations"""
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

def configure_environment():
    """Configure environment variables and system settings"""
    try:
        # Set Streamlit-specific configurations
        os.environ['STREAMLIT_SERVER_PORT'] = str(STREAMLIT_PORT)
        os.environ['STREAMLIT_SERVER_ADDRESS'] = STREAMLIT_HOST
        os.environ['STREAMLIT_SERVER_BASE_URL'] = STREAMLIT_BASE_URL
        os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
        os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'

        # Set application-specific configurations
        os.environ['API_SERVER_HOST'] = f"http://{API_HOST}:{API_PORT}"
        os.environ['WEBRTC_SERVER_HOST'] = f"ws://{WEBRTC_HOST}:{WEBRTC_PORT}"

        logger.info("Environment configuration completed successfully")
    except Exception as e:
        logger.error(f"Error configuring environment: {str(e)}")
        raise

async def initialize_services():
    """Initialize all required services and dependencies"""
    try:
        # Initialize database
        await asyncio.to_thread(init_db)
        logger.info("Database initialization completed")

        # Initialize session state
        initialize_session_state()
        logger.info("Session state initialized")

        # Initialize i18n manager
        i18n = I18nManager()
        logger.info("I18n manager initialized")

        return True
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        raise

async def main():
    try:
        # Initialize session state first with enhanced error handling
        try:
            if not st.session_state.get('_session_initialized'):
                initialize_session_state()
                st.session_state['_session_initialized'] = True
                logger.info("Session state initialized successfully")
                
                # Initialize role-specific session variables
                st.session_state.setdefault('user_role', None)
                st.session_state.setdefault('permissions', [])
                logger.info("Role-specific session variables initialized")
        except Exception as e:
            logger.error(f"Session state initialization error: {str(e)}", exc_info=True)
            render_error_page("""
                Error al iniciar la sesión. Por favor:
                1. Limpie la caché del navegador
                2. Cierre todas las pestañas de la aplicación
                3. Intente nuevamente
                
                Si el problema persiste, contacte al administrador.
                Detalles técnicos: {str(e)}
            """)
            return

        # Verify and configure environment with enhanced validation
        try:
            verify_environment()
            configure_environment()
            logger.info("Environment configured successfully")
        except Exception as e:
            logger.error(f"Environment configuration error: {str(e)}", exc_info=True)
            render_error_page(f"""
                Error en la configuración del entorno. 
                Por favor, contacte al administrador proporcionando el siguiente código de error:
                {hash(str(e))[:8]}
                
                Detalles técnicos: {str(e)}
            """)
            return

        # Configure page settings
        try:
            configure_page()
            logger.info("Page configuration completed")
        except Exception as e:
            logger.error(f"Page configuration error: {str(e)}")
            render_error_page(f"Error en la configuración de la página: {str(e)}")
            return

        # Initialize services with enhanced error handling
        try:
            await initialize_services()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Service initialization error: {str(e)}", exc_info=True)
            render_error_page(f"Error al inicializar servicios: {str(e)}. Por favor, intente nuevamente.")
            return

        # Enhanced authentication verification with detailed session state validation
        try:
            if not await handle_auth_middleware():
                logger.warning("Authentication failed or not completed")
                st.error("""
                    Error de autenticación. Por favor:
                    1. Verifique sus credenciales
                    2. Inicie sesión nuevamente
                    
                    Si el problema persiste, contacte al administrador.
                """)
                return
                
            # Verify role is properly set in session
            if not st.session_state.get('user_role'):
                logger.error("User role not set in session after authentication")
                st.error("""
                    Error en la configuración del rol de usuario.
                    Por favor, cierre sesión e inicie sesión nuevamente.
                """)
                return
                
            logger.info(f"Authentication successful - User Role: {st.session_state.get('user_role')}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            render_error_page(f"Error en la autenticación: {str(e)}. Por favor, intente nuevamente.")
            return

        # Verify role and permissions with enhanced checks
        role = st.session_state.get('role')
        if not role:
            logger.warning("No role found in session")
            st.error("Rol de usuario no encontrado")
            return
        
        if not check_role(role):
            logger.warning(f"Insufficient permissions for role: {role}")
            st.error("No tiene permisos suficientes para acceder a esta sección")
            return
        
        logger.info(f"Role verification successful for role: {role}")

        # Render dashboard with comprehensive error handling
        try:
            dashboard_app = DashboardApp()
            await dashboard_app.run()
            logger.info("Dashboard rendered successfully")
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}", exc_info=True)
            render_error_page(f"Error en el dashboard: {str(e)}")

    except Exception as e:
        logger.critical(f"Critical application error: {str(e)}", exc_info=True)
        render_error_page("Error crítico en la aplicación. Por favor, contacte al administrador.")

def configure_environment():
    """Configurar variables de entorno y ajustes iniciales"""
    os.environ['STREAMLIT_SERVER_PORT'] = str(STREAMLIT_PORT)
    os.environ['STREAMLIT_SERVER_ADDRESS'] = STREAMLIT_HOST
    os.environ['STREAMLIT_SERVER_BASEURL'] = STREAMLIT_BASE_URL
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

def configure_page():
    """Configurar la página de Streamlit"""
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

def render_auth_page():
    """Renderizar página de autenticación"""
    st.title("Sistema de Gestión de Casos")
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    with tab1:
        render_login_form()
    with tab2:
        render_register_form()

def render_error_page(error_msg):
    """Renderizar página de error"""
    st.error("Ha ocurrido un error")
    st.write(error_msg)
    if st.button("Reiniciar aplicación"):
        st.session_state.clear()
        st.experimental_rerun()

async def handle_auth_middleware():
    """Manejar middleware de autenticación"""
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

if __name__ == "__main__":
    try:
        logger.info("Iniciando aplicación...")
        asyncio.run(main())
        logger.info("Aplicación iniciada correctamente")
    except Exception as e:
        logger.critical(f"Error fatal en la aplicación: {str(e)}")