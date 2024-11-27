from utils.auth_utils import verify_token

def AuthMiddleware(get_response):
    def middleware(request):
        try:
            token = request.headers.get('Authorization')
            if not token:
                raise ValueError("Token no proporcionado")

            user_data = verify_token(token)
            request.user = user_data  # Agrega datos del usuario autenticado
        except Exception as e:
            # Registra el error y muestra un mensaje genérico
            logger.error(f"Error en middleware de autenticación: {e}")
            raise ValueError("Error crítico en la aplicación. Por favor, contacte al administrador.")

        return get_response(request)

    return middleware
