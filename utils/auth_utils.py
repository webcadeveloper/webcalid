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

def check_authentication():
    """Verifies if the user is authenticated in the current session."""
    try:
        if 'user_id' not in st.session_state:
            logger.warning("Authentication check failed: No user_id in session")
            st.error("No estás autenticado. Por favor, inicia sesión.")
            st.stop()
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking authentication: {str(e)}")
        st.error("Error verificando autenticación.")
        st.stop()
        return False

def is_authenticated() -> bool:
    """Checks if user is currently authenticated with enhanced validation."""
    try:
        # Check for required session variables
        required_keys = ['user_id', 'username']
        authenticated = all(key in st.session_state for key in required_keys)

        if authenticated:
            # Validate session consistency
            if not st.session_state.user_id or not st.session_state.username:
                logger.warning("Invalid session state detected")
                return False

            logger.info(f"User authenticated - ID: {st.session_state.user_id}, Username: {st.session_state.username}")
        else:
            logger.warning("User not authenticated - Missing required session data")

        return bool(authenticated)  # Ensure boolean return type
    except Exception as e:
        logger.error(f"Error checking authentication status: {str(e)}", exc_info=True)
        return False

def check_role(required_role) -> bool:
    """Verifica si el usuario tiene el rol adecuado para acceder a una sección"""
    try:
        if not is_authenticated():
            logger.warning("Role check failed: User not authenticated")
            st.error("Por favor, inicie sesión para continuar.")
            st.stop()
            return False

        # Verifica si el rol está en la sesión
        if 'user_role' not in st.session_state:
            logger.warning("Role check failed: User role not in session")
            st.error("No se pudo verificar el rol del usuario. Inicie sesión nuevamente.")
            st.stop()
            return False

        user_role = st.session_state.user_role

        # Verifica si el rol del usuario es el requerido
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

def logout():
    """Clear all session state variables."""
    try:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        logger.info("User logged out successfully")
        return True
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return False
