import sqlite3

def update_users_table():
    conn = sqlite3.connect('cases_database.db')
    cursor = conn.cursor()

    try:
        # Agregar columna role a la tabla users
        cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN role TEXT DEFAULT 'operator'
        """)

        # Actualizar el usuario admin como manager
        cursor.execute("""
        UPDATE users 
        SET role = 'manager' 
        WHERE username = 'admin'
        """)

        conn.commit()
        print("Tabla users actualizada exitosamente")
    except sqlite3.Error as e:
        print(f"Error al actualizar la tabla: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_users_table()