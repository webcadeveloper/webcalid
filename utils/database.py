import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor
from auth import verify_password, hash_password

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        database=os.environ.get('PGDATABASE', 'postgres'),
        user=os.environ.get('PGUSER', 'postgres'),
        password=os.environ.get('PGPASSWORD', 'postgres'),
        port=os.environ.get('PGPORT', '5432')
    )

def init_db():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        port=os.environ['PGPORT']
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Crear tabla de usuarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            role_id INTEGER REFERENCES user_roles(id)
        );
    """)

    # Crear tabla de roles de usuario
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        );
    """)

    # Crear tabla de llamadas telefónicas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS phone_calls (
            id SERIAL PRIMARY KEY,
            search_id INTEGER,
            phone_number VARCHAR(20),
            call_status VARCHAR(50),
            call_duration INTEGER,
            call_notes TEXT,
            call_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Crear tabla de formularios de verificación
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verification_forms (
            id SERIAL PRIMARY KEY,
            search_id INTEGER,
            verified_by INTEGER REFERENCES users(id),
            form_data JSONB,
            status VARCHAR(50),
            notes TEXT,
            verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

def add_phone_call(user_id, phone_number, status, duration, notes):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO phone_calls 
        (search_id, phone_number, call_status, call_duration, call_notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (user_id, phone_number, status, duration, notes)
    )
    call_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return call_id

def get_phone_calls(search_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM phone_calls WHERE search_id = %s ORDER BY call_date DESC",
        (search_id,)
    )
    calls = cur.fetchall()
    cur.close()
    conn.close()
    return calls

def add_verification_form(search_id, verified_by, form_data, status, notes):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO verification_forms 
        (search_id, verified_by, form_data, status, notes)
        VALUES (%s, %s, %s::jsonb, %s, %s)
        RETURNING id
        """,
        (search_id, verified_by, json.dumps(form_data), status, notes)
    )
    form_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return form_id

def get_verification_forms(search_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM verification_forms WHERE search_id = %s ORDER BY verification_date DESC",
        (search_id,)
    )
    forms = cur.fetchall()
    cur.close()
    conn.close()
    return forms