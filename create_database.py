import sqlite3

def create_new_db():
    # Conectar a la base de datos (esto crea la base de datos si no existe)
    conn = sqlite3.connect('/home/runner/SmartDashboardManager/eoir_scraper/database.db')
    cursor = conn.cursor()

    # Ejecutar el archivo SQL para crear la tabla 'cases'
    with open('create_database.sql', 'r') as file:
        sql_script = file.read()
        cursor.executescript(sql_script)

    # Confirmar la creación
    conn.commit()
    conn.close()

    print("Nueva base de datos y tabla 'cases' creada exitosamente.")

# Llamar a la función para crear la base de datos y la tabla
if __name__ == "__main__":
    create_new_db()
