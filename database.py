import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            database=os.environ.get('PGDATABASE', 'postgres'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', 'postgres'),
            port=os.environ.get('PGPORT', '5432')
        )
    except psycopg2.Error as e:
        logger.error(f"Unable to connect to the database: {e}")
        raise

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Check if the users table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        table_exists = cur.fetchone()[0]

        if not table_exists:
            # Create users table
            cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    role VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Check and add missing columns
            columns_to_check = [
                ('email', 'VARCHAR(100) UNIQUE NOT NULL'),
                ('password_hash', 'TEXT NOT NULL'),
                ('first_name', 'VARCHAR(50)'),
                ('last_name', 'VARCHAR(50)'),
                ('role', 'VARCHAR(20) NOT NULL'),
                ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            ]
            for column, data_type in columns_to_check:
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'users' AND column_name = '{column}'
                    );
                """)
                column_exists = cur.fetchone()[0]
                if not column_exists:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {column} {data_type};")
                    logger.info(f"Added missing column '{column}' to users table")

        # Create password_reset_tokens table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                token VARCHAR(100) UNIQUE NOT NULL,
                expiration TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create cases table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id SERIAL PRIMARY KEY,
                number VARCHAR(50) UNIQUE NOT NULL,
                status VARCHAR(20) NOT NULL,
                is_positive BOOLEAN NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                a_number VARCHAR(9) NOT NULL,
                court_address TEXT NOT NULL,
                court_phone VARCHAR(20) NOT NULL,
                client_phone VARCHAR(20),
                other_client_phone VARCHAR(20),
                client_address TEXT,
                client_email VARCHAR(100),
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("Database initialized successfully")
    except psycopg2.Error as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def execute_query(query, params=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(query, params)
        conn.commit()
        return cur.fetchall()
    except psycopg2.Error as e:
        logger.error(f"Database query error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    query = "SELECT * FROM users WHERE username = %s"
    result = execute_query(query, (username,))
    return result[0] if result else None

def update_user_profile(user_id, updates):
    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    query = f"UPDATE users SET {set_clause} WHERE id = %s"
    params = list(updates.values()) + [user_id]
    execute_query(query, params)

def insert_case(case_data):
    query = """
        INSERT INTO cases (number, status, is_positive, first_name, last_name, a_number,
                           court_address, court_phone, client_phone, other_client_phone,
                           client_address, client_email, created_by)
        VALUES (%(number)s, %(status)s, %(is_positive)s, %(first_name)s, %(last_name)s, %(a_number)s,
                %(court_address)s, %(court_phone)s, %(client_phone)s, %(other_client_phone)s,
                %(client_address)s, %(client_email)s, %(created_by)s)
        RETURNING id
    """
    result = execute_query(query, case_data)
    return result[0]['id'] if result else None

def get_cases_by_user(user_id):
    query = "SELECT * FROM cases WHERE created_by = %s ORDER BY created_at DESC"
    return execute_query(query, (user_id,))

