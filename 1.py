import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="ep-hidden-union-a5fp7shl.us-east-2.aws.neon.tech",
        database="neondb",
        user="neondb_owner",
        password="eMmFGk6v3YBX"
    )

try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users LIMIT 1")
    print(cur.fetchone())
    cur.close()
    conn.close()
    print("Conexión a la base de datos exitosa.")
except psycopg2.Error as e:
    print(f"Error al conectar a la base de datos: {e}")