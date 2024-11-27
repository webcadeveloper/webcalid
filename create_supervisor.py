import sqlite3
import hashlib

def create_supervisor():
    conn = sqlite3.connect('cases_database.db')
    cursor = conn.cursor()
    
    try:
        # Datos del supervisor
        username = 'supervisor'
        password = 'supervisor123'  # Contraseña inicial
        email = 'supervisor@example.com'
        
        # Hash de la contraseña
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertar el supervisor
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, password_hash, email, role)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, email, 'supervisor'))
        
        conn.commit()
        print("""
        Supervisor creado exitosamente:
        Username: supervisor
        Password: supervisor123
        Role: supervisor
        """)
    except sqlite3.Error as e:
        print(f"Error al crear el supervisor: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_supervisor()
