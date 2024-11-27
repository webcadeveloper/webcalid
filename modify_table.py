import sqlite3

def modify_users_table():
    conn = sqlite3.connect('/home/runner/SmartDashboardManager/eoir_scraper/database.db')
    cursor = conn.cursor()

    # Agregar las nuevas columnas si no existen
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN address TEXT')
    except sqlite3.OperationalError:
        print("La columna 'address' ya existe.")

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        print("La columna 'email' ya existe.")

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN others TEXT')
    except sqlite3.OperationalError:
        print("La columna 'others' ya existe.")

    # Confirmar cambios
    conn.commit()
    conn.close()

# Ejecutar la modificación de la tabla
modify_users_table()
