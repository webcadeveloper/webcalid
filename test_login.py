import sqlite3
import hashlib

def test_login(username, password):
    print(f"\nProbando login para usuario: {username}")

    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('cases_database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Obtener hash de la contraseña proporcionada
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"Hash generado para la contraseña: {password_hash}")

        # Buscar usuario
        cursor.execute("""
            SELECT id, username, password_hash, role 
            FROM users 
            WHERE username = ?
        """, (username,))

        user = cursor.fetchone()

        if user:
            print("\nUsuario encontrado:")
            print(f"ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Role: {user['role']}")
            print(f"Password hash almacenado: {user['password_hash']}")

            if user['password_hash'] == password_hash:
                print("\n✅ Login exitoso - Hash coincide")
            else:
                print("\n❌ Login fallido - Hash no coincide")
        else:
            print("\n❌ Usuario no encontrado")

    except sqlite3.Error as e:
        print(f"\n❌ Error en la base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Probar con las credenciales del supervisor
    test_login('supervisor', 'supervisor123')