class I18nManager:
    def __init__(self):
        # Inicializar con un diccionario de traducciones
        self.translations = {
            'es': {
                'dashboard.title': 'Panel de Control',
                'auth.welcome': 'Bienvenido',
                'auth.login': 'Iniciar Sesión',
                'auth.register': 'Registrarse',
                'auth.username': 'Nombre de Usuario',
                'auth.password': 'Contraseña',
                'auth.confirm_password': 'Confirmar Contraseña',
                'auth.role': 'Rol',
                'auth.invalid_credentials': 'Credenciales inválidas',
                'auth.registration_success': 'Registro exitoso',
                'auth.registration_failed': 'Error en el registro',
                'auth.passwords_dont_match': 'Las contraseñas no coinciden',
                'auth.username_too_short': 'El nombre de usuario es demasiado corto',
                'auth.password_too_short': 'La contraseña es demasiado corta'
            }
        }

    def get_text(self, key):
        # Obtener el idioma actual (podrías almacenarlo en st.session_state)
        lang = st.session_state.get('language', 'es')
        return self.translations.get(lang, {}).get(key, key)

