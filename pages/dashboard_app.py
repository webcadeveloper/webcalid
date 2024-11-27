import streamlit as st
import logging
from database import get_db_connection
from auth import verify_password, hash_password

class DashboardApp:
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()

    def setup_page_config(self):
        st.set_page_config(
            page_title="Sistema de Gestión de Casos",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self.apply_custom_styles()

    def apply_custom_styles(self):
        st.markdown("""
        <style>
        /* Add your custom styles here */
        </style>
        """, unsafe_allow_html=True)

    def initialize_session_state(self):
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'role' not in st.session_state:
            st.session_state.role = None
        if 'language' not in st.session_state:
            st.session_state.language = 'es'

    def authenticate_user(self, username, password, remember_me):
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)

        logger.debug(f"Intentando autenticar usuario: {username}")

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (username,))
            user_data = cur.fetchone()

            if user_data:
                user_id, stored_hash, role = user_data

                if verify_password(stored_hash, password):
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.session_state.role = role

                    if remember_me:
                        # Implement remember me logic here
                        pass

                    st.success("Inicio de sesión exitoso.")
                    self.render_profile_editor()
                else:
                    st.error("Nombre de usuario o contraseña incorrectos.")
            else:
                st.error("Nombre de usuario o contraseña incorrectos.")
        except Exception as e:
            logger.error(f"Error al autenticar usuario: {e}")
            st.error("Ocurrió un error al iniciar sesión. Por favor, inténtalo de nuevo más tarde.")
        finally:
            cur.close()
            conn.close()

    def register_user(self, username, password, confirm_password, email, first_name, last_name, role, terms):
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cur.fetchone()
            if existing_user:
                st.error("El nombre de usuario ya está en uso.")
                return

            if password != confirm_password:
                st.error("Las contraseñas no coinciden.")
                return

            hashed_password = hash_password(password)

            cur.execute("""
                INSERT INTO users (username, password_hash, email, first_name, last_name, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, hashed_password, email, first_name, last_name, role))
            conn.commit()

            st.success("Registro exitoso. Por favor, inicie sesión.")
            self.render_login_form()
        except Exception as e:
            logging.error(f"Error al registrar usuario: {e}")
            st.error("Ocurrió un error al registrar el usuario.")
        finally:
            cur.close()
            conn.close()

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
                st.markdown("[¿Olvidaste tu contraseña?](#)", unsafe_allow_html=True)

            submitted = st.form_submit_button("Iniciar Sesión")
            if submitted:
                self.authenticate_user(username, password, remember_me)
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
                self.register_user(username, password, confirm_password, email, first_name, last_name, role, terms)
        st.markdown("</div>", unsafe_allow_html=True)

    def render_profile_editor(self):
        if not st.session_state.user_id:
            return

        st.markdown("<div class='profile-section'>", unsafe_allow_html=True)
        st.subheader("Editar Perfil")

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT username, email, first_name, last_name, role, created_at
                FROM users WHERE id = %s
            """, (st.session_state.user_id,))
            user_data = cur.fetchone()

            if user_data:
                col1, col2 = st.columns(2)
                with col1:
                    new_first_name = st.text_input("Nombre", value=user_data[2] or "")
                    new_email = st.text_input("Email", value=user_data[1] or "")
                    current_password = st.text_input("Contraseña Actual", type="password")
                with col2:
                    new_last_name = st.text_input("Apellido", value=user_data[3] or "")
                    new_password = st.text_input("Nueva Contraseña", type="password")
                    confirm_new_password = st.text_input("Confirmar Nueva Contraseña", type="password")

                if st.button("Actualizar Perfil"):
                    if current_password:
                        cur.execute("SELECT password_hash FROM users WHERE id = %s", 
                                  (st.session_state.user_id,))
                        stored_hash = cur.fetchone()[0]

                        if verify_password(stored_hash, current_password):
                            updates = []
                            values = []

                            if new_first_name != user_data[2]:
                                updates.append("first_name = %s")
                                values.append(new_first_name)

                            if new_last_name != user_data[3]:
                                updates.append("last_name = %s")
                                values.append(new_last_name)

                            if new_email != user_data[1]:
                                updates.append("email = %s")
                                values.append(new_email)

                            if new_password:
                                if new_password == confirm_new_password:
                                    updates.append("password_hash = %s")
                                    values.append(hash_password(new_password))
                                else:
                                    st.error("Las nuevas contraseñas no coinciden")
                                    return

                            if updates:
                                values.append(st.session_state.user_id)
                                query = f"""
                                    UPDATE users 
                                    SET {", ".join(updates)}
                                    WHERE id = %s
                                """
                                cur.execute(query, values)
                                conn.commit()
                                st.success("Perfil actualizado correctamente")
                                st.rerun()
                        else:
                            st.error("Contraseña actual incorrecta")
                    else:
                        st.error("Por favor, ingrese su contraseña actual para realizar cambios")

                st.markdown("### Información de la Cuenta")
                st.write(f"**Usuario:** {user_data[0]}")
                st.write(f"**Rol:** {user_data[4]}")
                st.write(f"**Fecha de Registro:** {user_data[5]}")

        except Exception as e:
            logging.error(f"Error al editar perfil de usuario: {e}")
            st.error("Ocurrió un error al actualizar el perfil. Por favor, inténtalo de nuevo más tarde.")
        finally:
            cur.close()
            conn.close()

        st.markdown("</div>", unsafe_allow_html=True)

    def run(self):
        if not st.session_state.user_id:
            tab1, tab2 = st.tabs(["Iniciar Sesión", "Registro"])
            with tab1:
                self.render_login_form()
            with tab2:
                self.render_register_form()
        else:
            self.render_profile_editor()

