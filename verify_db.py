import sqlite3

def check_database():
    print("Iniciando verificación de la base de datos...")

    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('cases_database.db')
        cursor = conn.cursor()

        # 1. Verificar si la tabla users existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users';
        """)
        if cursor.fetchone():
            print("\n✅ La tabla 'users' existe")
        else:
            print("\n❌ La tabla 'users' no existe")
            return

        # 2. Mostrar la estructura de la tabla users
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        print("\nEstructura de la tabla users:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")

        # 3. Verificar usuarios existentes
        cursor.execute("SELECT id, username, role, email FROM users;")
        users = cursor.fetchall()
        print("\nUsuarios en la base de datos:")
        if users:
            for user in users:
                print(f"\nID: {user[0]}")
                print(f"Username: {user[1]}")
                print(f"Role: {user[2]}")
                print(f"Email: {user[3]}")
        else:
            print("No hay usuarios registrados")

        # 4. Verificar específicamente el usuario supervisor
        cursor.execute("""
            SELECT id, username, role, email 
            FROM users 
            WHERE username = 'supervisor';
        """)
        supervisor = cursor.fetchone()
        print("\nBuscando usuario 'supervisor':")
        if supervisor:
            print(f"✅ Usuario supervisor encontrado:")
            print(f"ID: {supervisor[0]}")
            print(f"Username: {supervisor[1]}")
            print(f"Role: {supervisor[2]}")
            print(f"Email: {supervisor[3]}")
        else:
            print("❌ Usuario supervisor no encontrado")

    except sqlite3.Error as e:
        print(f"\n❌ Error en la base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()