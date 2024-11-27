import sqlite3

# Función para inicializar la base de datos
def init_db():
    # Conectar a la base de datos SQLite (esto creará el archivo de base de datos si no existe)
    connection = sqlite3.connect('smart_dashboard.db')
    cursor = connection.cursor()

    # Leer el archivo SQL
    with open('init_db.sql', 'r') as sql_file:
        cursor.executescript(sql_file.read())  # Ejecutar el script SQL

    # Confirmar los cambios y cerrar la conexión
    connection.commit()
    cursor.close()
    connection.close()

# Ejecutar la inicialización
if __name__ == "__main__":
    init_db()
