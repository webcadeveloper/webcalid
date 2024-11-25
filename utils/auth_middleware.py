import jwt
import datetime
import streamlit as st

class AuthMiddleware:
    SECRET_KEY = "tu_clave_secreta"

    def is_authenticated(self) -> bool:
        return 'user_id' in st.session_state and 'token' in st.session_state

    @staticmethod
    def login(user_id: int, role: str) -> None:
        st.session_state.user_id = user_id
        st.session_state.user_role = role
        st.session_state.token = AuthMiddleware.create_token(user_id, role)

    @staticmethod
    def create_token(user_id: int, role: str) -> str:
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        }
        return jwt.encode(payload, AuthMiddleware.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def logout() -> None:
        for key in ['token', 'user_id', 'user_role']:
            if key in st.session_state:
                del st.session_state[key]