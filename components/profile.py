import streamlit as st
from database import get_db_connection
from utils import hash_password, I18nManager

class ProfileManager:
    def __init__(self):
        self.i18n = I18nManager()
        self._ = self.i18n.get_text
        self.conn = get_db_connection()

    def render(self):
        st.title(self._("profile.title"))
        user_data = self._get_user_data()

        col1, col2 = st.columns(2)
        with col1:
            self._render_user_info(user_data)
        with col2:
            self._render_api_config(user_data)

        self._render_update_button(user_data)

    def _get_user_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT username, pdl_api_key, ssid, display_name 
            FROM users WHERE id = %s
        """, (st.session_state.user_id,))
        data = cur.fetchone()
        cur.close()

        return {
            "username": data[0],
            "pdl_api_key": data[1],
            "ssid": data[2],
            "display_name": data[3]
        }

    def _render_user_info(self, user_data):
        st.subheader(self._("profile.user_info"))
        new_values = {}

        new_values["display_name"] = st.text_input(
            self._("profile.display_name"),
            value=user_data["display_name"]
        )

        new_values["username"] = st.text_input(
            self._("profile.username"),
            value=user_data["username"]
        )

        new_values["password"] = st.text_input(
            self._("profile.new_password"),
            type="password"
        )

        new_values["confirm_password"] = st.text_input(
            self._("profile.confirm_password"),
            type="password"
        )

        return new_values

    def _render_api_config(self, user_data):
        st.subheader(self._("profile.api_config"))
        new_values = {}

        new_values["ssid"] = st.text_input(
            self._("profile.ssid"),
            value=user_data["ssid"]
        )

        new_values["pdl_api_key"] = st.text_input(
            self._("profile.pdl_key"),
            value=user_data["pdl_api_key"],
            type="password"
        )

        return new_values

    def _render_update_button(self, original_data):
        if st.button(self._("profile.update"), type="primary"):
            self._handle_update(original_data)

    def _handle_update(self, original_data):
        update_fields = []
        update_values = []

        # Collect and validate changes
        if self._validate_changes(original_data, update_fields, update_values):
            try:
                self._save_changes(update_fields, update_values)
                st.success(self._("profile.update_success"))
                st.rerun()
            except Exception as e:
                st.error(f"{self._('profile.update_error')}: {str(e)}")

    def _validate_changes(self, original_data, fields, values):
        # Implementar validaciones específicas
        return True

    def _save_changes(self, fields, values):
        if not fields:
            return

        values.append(st.session_state.user_id)
        query = f"""
            UPDATE users 
            SET {", ".join(fields)}
            WHERE id = %s
        """

        cur = self.conn.cursor()
        cur.execute(query, values)
        self.conn.commit()
        cur.close()

def render_profile():
    profile = ProfileManager()
    profile.render()