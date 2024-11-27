import sqlite3

def create_users_table():
    conn = sqlite3.connect('/home/runner/SmartDashboardManager/eoir_scraper/database.db')
    cursor = conn.cursor()

    # Crear la tabla si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        a_number TEXT NOT NULL UNIQUE,
        court_address TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        address TEXT,
        email TEXT,
        others TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print("Tabla 'users' creada (si no existía).")

# Ejecutar la creación de la tabla
create_users_table()
