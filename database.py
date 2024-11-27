import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
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
    """Initialize the database by creating necessary tables."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Drop and recreate tables (for development purposes)
        cur.execute("DROP TABLE IF EXISTS cases CASCADE")
        cur.execute("DROP TABLE IF EXISTS users CASCADE")

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

        # Create cases table
        cur.execute("""
            CREATE TABLE cases (
                id SERIAL PRIMARY KEY,
                number VARCHAR(50) UNIQUE NOT NULL,
                status VARCHAR(20) NOT NULL,
                is_positive BOOLEAN NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                a_number VARCHAR(9) UNIQUE NOT NULL,
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
        raise
    finally:
        cur.close()
        conn.close()

def execute_query(query, params=None):
    """Execute a query and return the result."""
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

def login_user(username, password):
    """Login user and return user data."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Buscar usuario
        cur.execute("""
            SELECT * FROM users 
            WHERE username = %s
        """, (username,))

        user = cur.fetchone()

        if user:
            logger.debug(f"User found: {user['username']}")
            from utils.auth_utils import verify_password
            if verify_password(user['password_hash'], password):
                logger.info(f"Login successful for user: {username}")
                return True, user
            else:
                logger.warning(f"Invalid password for user: {username}")
        else:
            logger.warning(f"User not found: {username}")

        return False, None
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return False, None
    finally:
        cur.close()
        conn.close()

def register_user(username, password_hash, email, first_name, last_name, role):
    """Register a new user."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users 
            (username, email, password_hash, first_name, last_name, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, email, password_hash, first_name, last_name, role))

        user_id = cur.fetchone()
        conn.commit()

        if user_id:
            return True, "Usuario registrado exitosamente"
        else:
            return False, "Error inesperado al registrar el usuario"

    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "username" in str(e):
            return False, "El nombre de usuario ya está en uso"
        elif "email" in str(e):
            return False, "El correo electrónico ya está registrado"
        return False, "Error al registrar usuario"
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in register: {e}")
        return False, "Error interno del servidor"
    finally:
        cur.close()
        conn.close()

def get_user_by_username(username):
    """Get user by username."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT * FROM users 
            WHERE username = %s
        """, (username,))

        return cur.fetchone()
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_id(user_id):
    """Get user by ID."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT * FROM users 
            WHERE id = %s
        """, (user_id,))

        return cur.fetchone()
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def update_user_profile(user_id, updates):
    """Update user profile with given data."""
    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    query = f"UPDATE users SET {set_clause} WHERE id = %s"
    params = list(updates.values()) + [user_id]
    execute_query(query, params)

def insert_case(case_data):
    """Insert a new case into the database."""
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
    """Retrieve all cases created by a specific user."""
    query = "SELECT * FROM cases WHERE created_by = %s ORDER BY created_at DESC"
    return execute_query(query, (user_id,))

def verify_user_credentials(username, password):
    """Verify user credentials."""
    try:
        success, user = login_user(username, password)
        return user if success else None
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return None
