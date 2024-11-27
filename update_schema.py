import sqlite3

def update_database():
    conn = sqlite3.connect('cases_database.db')

    with open('update_schema.sql', 'r') as sql_file:
        sql_script = sql_file.read()

    try:
        conn.executescript(sql_script)
        print("Tablas creadas exitosamente")
    except sqlite3.Error as e:
        print(f"Error al crear las tablas: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()