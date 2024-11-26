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
            SELECT 
                username,
                pdl_api_key,
                ssid,
                display_name,
                sip_username,
                sip_password
            FROM users 
            WHERE id = %s
        """, (st.session_state.user_id,))
        data = cur.fetchone()
        cur.close()

        return {
            "username": data[0],
            "pdl_api_key": data[1],
            "ssid": data[2],
            "display_name": data[3],
            "sip_username": data[4] if len(data) > 4 else None,
            "sip_password": data[5] if len(data) > 5 else None
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
        
        # SSID Configuration with prominent styling and validation
        st.markdown("""
        <style>
        .ssid-warning {
            padding: 1rem;
            background-color: rgba(255, 165, 0, 0.1);
            border-left: 5px solid orange;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class='ssid-warning'>
        <h4>⚠️ Configuración de SSID</h4>
        <p>El SSID es <strong>requerido</strong> para realizar llamadas telefónicas.</p>
        <p>Para obtener su SSID:</p>
        <ol>
            <li>Contacte a Central Centric para solicitar su SSID único</li>
            <li>El SSID debe tener el formato: CC-XXXXX-YY</li>
            <li>Asegúrese de mantener su SSID seguro y no compartirlo</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

        ssid = st.text_input(
            "SSID de Central Centric",
            value=user_data["ssid"],
            help="Formato requerido: CC-XXXXX-YY"
        )

        if ssid:  # Add this check first
            if not ssid.startswith("CC-") or len(ssid.split("-")) != 3:
                st.error("El formato del SSID no es válido. Debe seguir el formato: CC-XXXXX-YY")
        new_values["ssid"] = ssid

        # PDL API Key Configuration - Only for admin users
        if st.session_state.get('user_role') == 'admin':
            st.markdown("""
            <div style='background-color: rgba(255, 0, 0, 0.1); border-left: 5px solid red; padding: 1rem; margin: 1rem 0;'>
                <h4>🔑 Configuración de PDL API</h4>
                <p>La API key de People Data Labs es <strong>requerida</strong> para usuarios administradores.</p>
                <p>Esta clave es necesaria para acceder a funcionalidades avanzadas de búsqueda.</p>
            </div>
            """, unsafe_allow_html=True)

            pdl_api_key = st.text_input(
                "PDL API Key (Requerida)",
                value=user_data["pdl_api_key"],
                type="password",
                help="API key de People Data Labs - Requerida para administradores"
            )

            if not pdl_api_key:
                st.error("La API key de PDL es requerida para usuarios administradores")
            new_values["pdl_api_key"] = pdl_api_key
        else:
            new_values["pdl_api_key"] = user_data["pdl_api_key"]

        # CallCentric Configuration
        st.markdown("""
        <style>
        .callcentric-config {
            background-color: rgba(0, 255, 0, 0.1);
            border-left: 5px solid #0f0;
            padding: 1rem;
            margin: 20px 0;
        }
        .callcentric-config h4 {
            color: #0f0;
            margin-bottom: 1rem;
        }
        .callcentric-config p, .callcentric-config li {
            color: #0ff;
        }
        .field-error {
            color: #ff4444;
            font-size: 0.9em;
            margin-top: 0.2rem;
        }
        </style>
        <div class='callcentric-config'>
        <h4>☎️ Configuración de CallCentric</h4>
        <p>Las credenciales de CallCentric son <strong>requeridas</strong> para realizar llamadas telefónicas.</p>
        <p>Servidor SIP: <strong>sip.callcentric.com</strong></p>
        <p>Para obtener sus credenciales:</p>
        <ol>
            <li>Registre una cuenta en CallCentric</li>
            <li>Configure su número SIP en el panel de CallCentric</li>
            <li>Use las credenciales proporcionadas por CallCentric</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

        st.text("Servidor SIP: sip.callcentric.com (fijo)")
        
        sip_username = st.text_input(
            "Usuario SIP de CallCentric",
            value=user_data.get("sip_username", ""),
            help="Tu nombre de usuario de CallCentric (formato: 1777XXXXXX)",
            key="sip_username"
        )

        if sip_username and not sip_username.startswith("1"):
            st.markdown("<p class='field-error'>El usuario SIP debe comenzar con '1' seguido de tu número CallCentric</p>", unsafe_allow_html=True)
        
        new_values["sip_username"] = sip_username

        sip_password = st.text_input(
            "Contraseña SIP de CallCentric",
            value=user_data.get("sip_password", ""),
            type="password",
            help="Tu contraseña de CallCentric (mínimo 8 caracteres)",
            key="sip_password"
        )

        if sip_password and len(sip_password) < 8:
            st.markdown("<p class='field-error'>La contraseña debe tener al menos 8 caracteres</p>", unsafe_allow_html=True)

        new_values["sip_password"] = sip_password

        # Validation status
        if sip_username and sip_password:
            if sip_username.startswith("1") and len(sip_password) >= 8:
                st.success("✅ Credenciales de CallCentric válidas")
            else:
                st.error("❌ Por favor, corrija los errores en las credenciales de CallCentric")

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
        """Validate changes before saving to database"""
        try:
            if 'sip_username' in st.session_state:
                sip_username = st.session_state.sip_username
                if sip_username and sip_username != original_data['sip_username']:
                    if not sip_username.startswith('1'):
                        st.error("El usuario SIP debe comenzar con '1'")
                        return False
                    fields.append("sip_username = %s")
                    values.append(sip_username)

            if 'sip_password' in st.session_state:
                sip_password = st.session_state.sip_password
                if sip_password and sip_password != original_data['sip_password']:
                    if len(sip_password) < 8:
                        st.error("La contraseña SIP debe tener al menos 8 caracteres")
                        return False
                    fields.append("sip_password = %s")
                    values.append(sip_password)

            return True
        except Exception as e:
            logger.error(f"Error validating changes: {e}")
            st.error("Error al validar los cambios")
            return False

    def _save_changes(self, fields, values):
        """Save validated changes to database"""
        if not fields:
            return

        try:
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
            
            st.success("Configuración actualizada correctamente")
            
        except Exception as e:
            logger.error(f"Error saving changes: {e}")
            st.error("Error al guardar los cambios en la base de datos")

def render_profile():
    profile = ProfileManager()
    profile.render()