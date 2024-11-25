import streamlit as st
from functools import wraps
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    AGENT = "agent"
    USER = "user"

def check_role(required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_role' not in st.session_state:
                st.error("No tiene permisos para acceder")
                st.stop()

            user_role = UserRole(st.session_state.user_role)
            if user_role.value not in required_roles:
                st.error("Acceso denegado")
                st.stop()

            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_role_permissions(role):
    permissions = {
        UserRole.ADMIN: ["all"],
        UserRole.SUPERVISOR: ["view_analytics", "manage_agents", "export_data"],
        UserRole.AGENT: ["search", "make_calls", "add_notes"],
        UserRole.USER: ["search"]
    }
    return permissions.get(role, [])