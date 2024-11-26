import streamlit as st
from utils import check_role, UserRole, I18nManager

class Navigation:
    def __init__(self):
        self.i18n = I18nManager()
        self._ = self.i18n.get_text

    def render(self):
        st.sidebar.title(self._("nav.title"))
        user_role = st.session_state.get('user_role', UserRole.USER)

        self._render_main_navigation(user_role)
        self._render_language_selector()
        self._render_logout()

    def _render_main_navigation(self, user_role):
        pages = self._get_available_pages(user_role)

        for page_name, page_data in pages.items():
            if page_data['visible']:
                if st.sidebar.button(self._(f"nav.{page_name}")):
                    st.query_params["page"] = page_data['url']
                    st.rerun()

    def _get_available_pages(self, user_role):
        pages = {
            "home": {
                "url": "/",
                "visible": True
            },
            "search": {
                "url": "/number_generator",
                "visible": True
            },
            "calls": {
                "url": "phone_call",
                "visible": user_role in [UserRole.AGENT, UserRole.SUPERVISOR, UserRole.ADMIN]
            },
            "supervisor": {
                "url": "/Supervisor_Dashboard",
                "visible": user_role in [UserRole.SUPERVISOR, UserRole.ADMIN]
            },
            "admin": {
                "url": "/admin",
                "visible": user_role == UserRole.ADMIN
            }
        }
        return pages

    def _render_language_selector(self):
        st.sidebar.selectbox(
            self._("nav.language"),
            ["es", "en"],
            key="language",
            on_change=self._handle_language_change
        )

    def _render_logout(self):
        if st.sidebar.button(self._("nav.logout")):
            st.session_state.clear()
            st.rerun()

    def _handle_language_change(self):
        st.rerun()

def render_navigation():
    nav = Navigation()
    nav.render()