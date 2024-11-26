import streamlit as st
import logging
from database import init_db, get_db_connection
from utils import (
    hash_password, verify_password,
    AuthMiddleware, I18nManager,
    UserRole, check_role
)
from components.navigation import render_navigation
from components.profile import render_profile
from pages.phone_call import PhoneCallPage
from utils.supervisor_analytics import SupervisorAnalytics
from utils.report_generator import ReportGenerator

init_db()
i18n = I18nManager()
_ = i18n.get_text
auth = AuthMiddleware()

class DashboardApp:
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()

    def setup_page_config(self):
        st.set_page_config(
            page_title=_("dashboard.title"),
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        self.apply_theme()

    def apply_theme(self):
        st.markdown("""
        <style>
        .matrix-theme {
            background-color: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            border: 1px solid #00ff00;
        }
        .stButton>button {
            background-color: rgba(0, 255, 0, 0.2);
            color: #00ff00;
            border: 1px solid #00ff00;
        }
        .stTextInput>div>div>input {
            color: #00ff00;
            background-color: rgba(0, 0, 0, 0.8);
        }
        div.stTabs > div > div > button {
            background-color: rgba(0, 255, 0, 0.1);
            color: #00ff00;
        }
        div.stTabs > div > div > button:hover {
            background-color: rgba(0, 255, 0, 0.2);
        }
        div.stTabs > div > div > button[data-baseweb="tab"][aria-selected="true"] {
            background-color: rgba(0, 255, 0, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)

    def initialize_session_state(self):
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'user_role' not in st.session_state:
            st.session_state.user_role = None
        if 'language' not in st.session_state:
            st.session_state.language = 'es'

    def run(self):
        if not st.session_state.get('user_id'):
            self.render_auth_pages()
            return

        render_navigation()
        current_page = st.query_params.get("page", "home")

        pages = {
            "home": render_profile,
            "Number_Search": lambda: __import__("pages.number_search").number_search_page(),
            "phone_call": lambda: __import__("pages.3_phone_call").page_render(),
            "Supervisor_Dashboard": lambda: SupervisorAnalytics().render(),
            "reports": lambda: ReportGenerator().render()
        }

        if current_page in pages:
            pages[current_page]()

    def render_auth_pages(self):
        st.title(_("auth.welcome"))
        tab1, tab2 = st.tabs([_("auth.login"), _("auth.register")])

        with tab1:
            self.handle_login()
        with tab2:
            self.handle_register()

    def handle_login(self):
        with st.form("login_form"):
            username = st.text_input(_("auth.username"))
            password = st.text_input(_("auth.password"), type="password")
            submitted = st.form_submit_button(_("auth.login"))

            if submitted:
                self.authenticate_user(username, password)

    def handle_register(self):
        with st.form("register_form"):
            username = st.text_input(_("auth.username"))
            password = st.text_input(_("auth.password"), type="password")
            confirm_password = st.text_input(_("auth.confirm_password"), type="password")
            role = st.selectbox(_("auth.role"), ["user", "agent", "supervisor"])
            submitted = st.form_submit_button(_("auth.register"))

            if submitted:
                self.register_user(username, password, confirm_password, role)

    def authenticate_user(self, username, password):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, password_hash, role 
                    FROM users 
                    WHERE username = %s
                """, (username,))
                user = cur.fetchone()

                if not user:
                    logging.warning(f"Login attempt failed: Username {username} not found")
                    st.error(_("auth.invalid_credentials"))
                    return False

                try:
                    if verify_password(user[1], password):
                        logging.info(f"User {username} successfully authenticated with role {user[2]}")
                        st.session_state.user_id = user[0]
                        st.session_state.user_role = user[2]
                        st.success(_("auth.login_success"))
                        st.rerun()
                        return True
                    else:
                        logging.warning(f"Login attempt failed: Invalid password for user {username}")
                        st.error(_("auth.invalid_credentials"))
                        return False
                except Exception as e:
                    logging.error(f"Password verification error for user {username}: {str(e)}")
                    st.error(_("auth.system_error"))
                    return False
        except Exception as e:
            logging.error(f"Authentication error for user {username}: {str(e)}")
            st.error(_("auth.system_error"))
            return False

    def register_user(self, username, password, confirm_password, role):
        if not self.validate_registration(username, password, confirm_password):
            return

        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                # Check if username already exists
                cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    logging.warning(f"Registration failed: Username {username} already exists")
                    st.error(_("auth.username_taken"))
                    return

                # Validate role
                valid_roles = ['user', 'agent', 'supervisor', 'admin']
                if role not in valid_roles:
                    logging.error(f"Registration failed: Invalid role {role}")
                    st.error(_("auth.invalid_role"))
                    return

                try:
                    hashed_password = hash_password(password)
                    logging.debug(f"Password hashed successfully for new user {username}")
                    cur.execute(
                        """
                        INSERT INTO users (username, password_hash, role) 
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (username, hashed_password, role)
                    )
                except Exception as e:
                    logging.error(f"Error hashing password during registration: {str(e)}")
                    raise
                user_id = cur.fetchone()[0]
                conn.commit()
                logging.info(f"User {username} successfully registered with role {role} (ID: {user_id})")
                st.success(_("auth.registration_success"))
        except Exception as e:
            logging.error(f"Registration error for user {username}: {str(e)}")
            st.error(_("auth.registration_failed"))

    def validate_registration(self, username, password, confirm_password):
        if password != confirm_password:
            st.error(_("auth.passwords_dont_match"))
            return False
        if len(username) < 3:
            st.error(_("auth.username_too_short"))
            return False
        if len(password) < 6:
            st.error(_("auth.password_too_short"))
            return False
        return True

def main():
    app = DashboardApp()
    app.run()

if __name__ == "__main__":
    main()

