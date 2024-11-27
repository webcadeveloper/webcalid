import streamlit as st
# ... (resto de imports)

class DashboardApp:
    # ... (resto del código)

    def render_profile_editor(self):
        # ... (código anterior)
                    try:
                        update_user_profile(st.session_state.user_id, updates)
                        st.success("Perfil actualizado correctamente")
                        st.experimental_rerun()  # Cambio aquí
                    except Exception as e:
                        logger.error(f"Error al actualizar perfil: {e}")
                        st.error("Ocurrió un error al actualizar el perfil. Por favor, inténtalo de nuevo más tarde.")

    def render_main_page(self):
        # ... (código anterior)
            if new_theme != current_theme:
                st.session_state.theme = new_theme
                st.experimental_rerun()  # Cambio aquí

            # User actions
            if st.button("🚪 Cerrar Sesión", type="secondary"):
                st.session_state.clear()
                st.experimental_rerun()  # Cambio aquí