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

def check_authentication():
    """Verifies if the user is authenticated in the current session."""
    if 'user_id' not in st.session_state:
        logger.warning("Authentication check failed: No user_id in session")
        st.error("No estás autenticado. Por favor, inicia sesión.")
        st.stop()

def check_role(required_role: str):
    """Verifies if the user has the required role."""
    try:
        if 'user_role' not in st.session_state:
            logger.warning("Role check failed: No role in session")
            st.error("No tienes permisos suficientes.")
            st.stop()
            return

        user_role = st.session_state.user_role
        if user_role != required_role:
            logger.warning(f"Role check failed: User has {user_role}, needs {required_role}")
            st.error("No tienes los permisos necesarios para esta acción.")
            st.stop()

    except Exception as e:
        logger.error(f"Error checking role: {str(e)}")
        st.error("Error verificando permisos de usuario.")
        st.stop()

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