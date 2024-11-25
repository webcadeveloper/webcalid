import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor

def get_db_connection():
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
    
    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            is_supervisor BOOLEAN DEFAULT FALSE
        );
    """)
    
    # Create search_history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            search_number VARCHAR(50) NOT NULL,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_found BOOLEAN DEFAULT FALSE
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def add_search_history(user_id, search_number, result_found, source_results=None):
    if source_results is None:
        source_results = {}
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO search_history 
        (user_id, search_number, result_found, source_results) 
        VALUES (%s, %s, %s, %s::jsonb)
        """,
        (user_id, search_number, result_found, json.dumps(source_results))
    )
    conn.commit()
    cur.close()
    conn.close()

def get_search_statistics():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            COUNT(*) as total_searches,
            SUM(CASE WHEN result_found THEN 1 ELSE 0 END) as successful_searches,
            DATE(search_date) as search_day
        FROM search_history
        GROUP BY DATE(search_date)
        ORDER BY search_day DESC
        LIMIT 30
    """)
    stats = cur.fetchall()
    cur.close()
    conn.close()
    return stats

def add_phone_call(search_id, phone_number, status="initiated", duration=None, notes=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO phone_calls 
            (search_id, phone_number, call_status, call_duration, call_notes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (search_id, phone_number, status, duration, notes)
        )
        call_id = cur.fetchone()[0]
        conn.commit()
        return call_id
    finally:
        cur.close()
        conn.close()

def add_verification_form(search_id, verified_by, form_data, status="submitted", notes=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
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
        return form_id
    finally:
        cur.close()
        conn.close()

def get_phone_calls(search_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT * FROM phone_calls WHERE search_id = %s ORDER BY call_date DESC",
            (search_id,)
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_verification_forms(search_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(
            "SELECT * FROM verification_forms WHERE search_id = %s ORDER BY verification_date DESC",
            (search_id,)
        )
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()