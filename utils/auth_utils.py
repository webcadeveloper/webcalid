import logging
import streamlit as st
import hashlib
import os

# Configuración básica de logging para errores
logging.basicConfig(level=logging.DEBUG)

def hash_password(password):
    """
    Crea un hash seguro de la contraseña utilizando SHA-256 y un salt aleatorio.

    Args:
        password (str): La contraseña a hashear.

    Returns:
        tuple: (salt, hashed_password)
    """
    salt = os.urandom(32)  # Genera un salt aleatorio de 32 bytes
    hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt, hashed_password

def check_authentication():
    if 'user_id' not in st.session_state:
        st.error("No estás autenticado. Por favor, inicia sesión.")
        st.stop()

def check_role(user, required_role):
    """
    Verifica si el usuario tiene el rol requerido.

    Args:
        user (dict): Diccionario que representa al usuario, debe tener una clave 'role'.
        required_role (str): El rol que se requiere para acceder a un recurso.

    Returns:
        bool: True si el usuario tiene el rol requerido, False en caso contrario.
    """
    try:
        # Verificar si el usuario tiene un rol asignado
        if 'role' not in user:
            logging.warning(f"El usuario {user} no tiene un rol asignado.")
            return False

        # Compara el rol del usuario con el rol requerido
        if user['role'] == required_role:
            logging.info(f"El usuario {user} tiene el rol adecuado: {required_role}.")
            return True
        else:
            logging.warning(f"El usuario {user} tiene el rol {user['role']}, pero se requiere {required_role}.")
            return False
    except Exception as e:
        logging.error(f"Error al verificar el rol del usuario: {e}")
        return False

def is_authenticated():
    """
    Verifica si el usuario está autenticado.

    Returns:
        bool: True si el usuario está autenticado, False si no lo está.
    """
    try:
        if 'user_id' in st.session_state:
            logging.info("Usuario autenticado correctamente.")
            return True
        else:
            logging.warning("El usuario no está autenticado.")
            return False
    except Exception as e:
        logging.error(f"Error al verificar la autenticación: {e}")
        return False

