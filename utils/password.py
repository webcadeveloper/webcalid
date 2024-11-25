import hashlib
import secrets
import base64

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return base64.b64encode(salt + password_hash).decode('utf-8')

def verify_password(stored_hash: str, provided_password: str) -> bool:
    try:
        decoded = base64.b64decode(stored_hash.encode('utf-8'))
        salt = decoded[:16]
        stored_password_hash = decoded[16:]

        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return secrets.compare_digest(new_hash, stored_password_hash)
    except Exception:
        return False