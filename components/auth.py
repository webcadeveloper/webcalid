import streamlit as st
from database import get_user_by_username
from utils.auth_utils import verify_password

def render_login_form():
    """Renderiza el formulario de login"""
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Iniciar Sesión")

        # Campos del formulario
        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")

        # Botón de submit
        submitted = st.form_submit_button("Iniciar Sesión")

        if submitted:
            if not username or not password:
                st.error("Por favor, complete todos los campos")
                return

            # Verificar credenciales
            user = get_user_by_username(username)
            if user and verify_password(password, user['password_hash']):
                # Guardar información en la sesión
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                st.session_state.role = user['role']
                st.session_state.authenticated = True

                st.success("¡Inicio de sesión exitoso!")
                st.experimental_rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

def render_register_form():
    """Renderiza el formulario de registro"""
    with st.form("register_form"):
        st.subheader("Registro de Usuario")

        # Campos del formulario
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Nombre")
        with col2:
            last_name = st.text_input("Apellido")

        username = st.text_input("Nombre de Usuario")
        email = st.text_input("Correo Electrónico")

        col3, col4 = st.columns(2)
        with col3:
            password = st.text_input("Contraseña", type="password")
        with col4:
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
            # Validaciones
            if not all([username, email, password, confirm_password]):
                st.error("Por favor complete todos los campos")
                return

            if password != confirm_password:
                st.error("Las contraseñas no coinciden")
                return

            if not terms:
                st.error("Debe aceptar los términos y condiciones")
                return

            # Intentar registro
            from database import register_user
            success, message = register_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role
            )

            if success:
                st.success(message)
                st.info("Por favor, inicie sesión con sus nuevas credenciales")
            else:
                st.error(message)