import sqlite3

def create_database():
    conn = sqlite3.connect('cases_database.db')

    with open('schema.sql', 'r') as sql_file:
        sql_script = sql_file.read()

    try:
        conn.executescript(sql_script)
        print("Base de datos creada exitosamente")
    except sqlite3.Error as e:
        print(f"Error al crear la base de datos: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_database()
    