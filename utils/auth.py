import streamlit as st
from utils.auth_utils import check_role

class AuthMiddleware:
    def __init__(self):
        self.authenticated = False
        self.user_role = None

    def is_authenticated(self):
        """
        Comprueba si el usuario está autenticado.
        """
        return self.authenticated

    def authenticate(self, username, password):
        """
        Autentica al usuario con el nombre de usuario y la contraseña proporcionados.
        Establece el estado de autenticación y el rol del usuario.
        """
        # Aquí iría el código para autenticar al usuario
        # utilizando la base de datos u otro sistema de autenticación
        if username == "admin" and password == "password":
            self.authenticated = True
            self.user_role = "supervisor"
            st.session_state.user_id = 1
            st.session_state.user_role = self.user_role
            st.success("¡Inicio de sesión exitoso!")
        else:
            st.error("Nombre de usuario o contraseña incorrectos")

    def register(self, username, password, role):
        """
        Registra un nuevo usuario con el nombre de usuario, la contraseña y el rol proporcionados.
        Establece el estado de autenticación y el rol del usuario.
        """
        # Aquí iría el código para registrar al usuario
        # en la base de datos u otro sistema de registro
        self.authenticated = True
        self.user_role = role
        st.session_state.user_id = 2
        st.session_state.user_role = self.user_role
        st.success("¡Registro exitoso!")

    def check_authorization(self, required_role):
        """
        Comprueba si el usuario actual tiene el rol requerido.
        Muestra un mensaje de advertencia y detiene la aplicación si el usuario no está autorizado.
        """
        check_role(required_role)