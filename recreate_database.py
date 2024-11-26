import os
import psycopg2

# URL de la base de datos
DATABASE_URL = "postgresql://neondb_owner:eMmFGk6v3YBX@ep-hidden-union-a5fp7shl.us-east-2.aws.neon.tech/neondb?sslmode=require"

def recreate_database():
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        print("Conectado a la base de datos.")

        # Leer el contenido del archivo SQL
        with open('recreate_database.sql', 'r') as file:
            sql_script = file.read()

        # Ejecutar el script SQL
        cur.execute(sql_script)
        print("La base de datos ha sido recreada exitosamente.")

    except (Exception, psycopg2.Error) as error:
        print("Error al recrear la base de datos:", error)

    finally:
        if conn:
            cur.close()
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    recreate_database()

