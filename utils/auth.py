# utils/auth.py
import logging
import streamlit as st
import hashlib
import os
import base64
import hmac

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Creates a secure password hash using PBKDF2 with a random salt."""
    try:
        salt = os.urandom(16)
        iterations = 100000
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt,
            iterations
        )

        combined = salt + hash_bytes
        encoded = base64.b64encode(combined).decode('utf-8')

        logger.debug("Password hashed successfully")
        return encoded

    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise RuntimeError("Error creating password hash")

def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    """Verifies a password against its hash."""
    try:
        decoded = base64.b64decode(stored_password_hash.encode('utf-8'))
        salt = decoded[:16]
        stored_hash = decoded[16:]

        iterations = 100000
        calculated_hash = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            iterations
        )

        matches = hmac.compare_digest(calculated_hash, stored_hash)
        logger.debug("Password verification completed")
        return matches

    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

async def check_authentication():
    """Verifies if the user is authenticated in the current session."""
    try:
        if 'user_id' not in st.session_state:
            logger.warning("Authentication check failed: No user_id in session")
            st.error("No estás autenticado. Por favor, inicia sesión.")
            st.stop()
            return False
        
        # Verify session validity
        if not await verify_session():
            logger.warning("Session verification failed")
            st.error("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
            st.stop()
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking authentication: {str(e)}")
        st.error("Error verificando autenticación")
        st.stop()
        return False

async def verify_session():
    """Verify if the current session is valid."""
    try:
        if not st.session_state.get('_session_initialized'):
            return False
            
        user_id = st.session_state.get('user_id')
        user_role = st.session_state.get('user_role')
        
        return bool(user_id and user_role)
    except Exception as e:
        logger.error(f"Error verifying session: {str(e)}")
        return False

def check_role(required_role: str) -> bool:
    """Verifies if the user has the required role."""
    try:
        if 'user_role' not in st.session_state:
            logger.warning("Role check failed: No role in session")
            st.error("No se encontró el rol del usuario en la sesión. Por favor, inicie sesión nuevamente.")
            st.stop()
            return False

        user_role = st.session_state.user_role
        if user_role != required_role:
            logger.warning(f"Role check failed: User has {user_role}, needs {required_role}")
            st.error(f"No tienes los permisos necesarios para esta acción. Se requiere el rol '{required_role}'.")
            st.stop()
            return False

        logger.info(f"Role check successful: User has required role '{required_role}'")
        return True

    except Exception as e:
        logger.error(f"Error checking role: {str(e)}", exc_info=True)
        st.error(f"Error verificando permisos de usuario: {str(e)}")
        st.stop()
        return False

def is_authenticated() -> bool:
    """Checks if user is currently authenticated."""
    try:
        authenticated = 'user_id' in st.session_state
        if authenticated:
            logger.info("User is authenticated")
        else:
            logger.warning("User is not authenticated")
        return authenticated
    except Exception as e:
        logger.error(f"Error checking authentication status: {str(e)}")
        return False

def logout():
    """Clear all session state variables."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]