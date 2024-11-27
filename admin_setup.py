from database import register_user
from utils.auth_utils import hash_password
import logging

def setup_admin_users():
    # Manager
    manager_data = {
        'username': 'admin_manager',
        'password': 'manager123',  # Cambia esto por una contraseña segura
        'email': 'manager@example.com',
        'first_name': 'Admin',
        'last_name': 'Manager',
        'role': 'manager'
    }

    # Supervisor
    supervisor_data = {
        'username': 'admin_supervisor',
        'password': 'supervisor123',  # Cambia esto por una contraseña segura
        'email': 'supervisor@example.com',
        'first_name': 'Admin',
        'last_name': 'Supervisor',
        'role': 'supervisor'
    }

    for user_data in [manager_data, supervisor_data]:
        password_hash = hash_password(user_data['password'])
        try:
            success, message = register_user(
                username=user_data['username'],
                password_hash=password_hash,
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role']
            )
            if success:
                print(f"Usuario {user_data['username']} creado exitosamente")
            else:
                logging.error(f"Error creando usuario {user_data['username']}: {message}")
        except Exception as e:
            logging.error(f"Error inesperado al crear usuario {user_data['username']}: {str(e)}")

if __name__ == "__main__":
    setup_admin_users()