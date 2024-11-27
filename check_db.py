# check_db.py
from database import get_db_connection
import psycopg2

def check_database_structure():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Verificar tablas existentes
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print("Tablas existentes:", tables)

        # Verificar estructura de la tabla users
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        columns = cur.fetchall()
        print("\nEstructura de la tabla users:")
        for column in columns:
            print(f"- {column[0]}: {column[1]}")

    except psycopg2.Error as e:
        print(f"Error verificando base de datos: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_database_structure()
