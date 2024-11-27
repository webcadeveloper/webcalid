import os
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt
from database import execute_query, get_user_by_username
import base64

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')  # Use an environment variable in production
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(days=1)

def hash_password(password):
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + pwdhash).decode('utf-8')

def verify_password(stored_password, provided_password):
    try:
        # Try to decode the stored password as base64
        decoded = base64.b64decode(stored_password)
        salt = decoded[:32]
        stored_pwdhash = decoded[32:]
    except:
        # If decoding fails, assume it's the old format (bytea)
        salt = stored_password[:32]
        stored_pwdhash = stored_password[32:]

    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash == stored_pwdhash

def create_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def register_user(username, password, email, first_name, last_name, role):
    hashed_password = hash_password(password)
    query = """
    INSERT INTO users (username, email, password_hash, first_name, last_name, role)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    """
    params = (username, email, hashed_password, first_name, last_name, role)
    try:
        result = execute_query(query, params)
        return True, "Usuario registrado exitosamente."
    except Exception as e:
        return False, f"Error al registrar usuario: {str(e)}"

def login_user(username, password):
    user = get_user_by_username(username)
    if user and verify_password(user['password_hash'], password):
        return True, user
    return False, None

def initiate_password_reset(email):
    query = "SELECT id FROM users WHERE email = %s"
    result = execute_query(query, (email,))
    if not result:
        return False, "No se encontró un usuario con ese correo electrónico."

    user_id = result[0]['id']
    token = secrets.token_urlsafe()
    expiration = datetime.utcnow() + timedelta(hours=1)

    query = """
    INSERT INTO password_reset_tokens (user_id, token, expiration)
    VALUES (%s, %s, %s)
    """
    execute_query(query, (user_id, token, expiration))

    # Here you would typically send an email with the reset link
    # For this example, we'll just return the token
    return True, f"Token de restablecimiento generado: {token}"

def reset_password(token, new_password):
    query = """
    SELECT user_id FROM password_reset_tokens
    WHERE token = %s AND expiration > %s AND used = FALSE
    """
    result = execute_query(query, (token, datetime.utcnow()))
    if not result:
        return False, "Token inválido o expirado."

    user_id = result[0]['user_id']
    hashed_password = hash_password(new_password)

    query = "UPDATE users SET password_hash = %s WHERE id = %s"
    execute_query(query, (hashed_password, user_id))

    query = "UPDATE password_reset_tokens SET used = TRUE WHERE token = %s"
    execute_query(query, (token,))

    return True, "Contraseña restablecida exitosamente."

def change_password(user_id, current_password, new_password):
    query = "SELECT password_hash FROM users WHERE id = %s"
    result = execute_query(query, (user_id,))
    if not result:
        return False, "Usuario no encontrado."

    stored_password = result[0]['password_hash']
    if not verify_password(stored_password, current_password):
        return False, "Contraseña actual incorrecta."

    hashed_password = hash_password(new_password)
    query = "UPDATE users SET password_hash = %s WHERE id = %s"
    execute_query(query, (hashed_password, user_id))

    return True, "Contraseña cambiada exitosamente."

