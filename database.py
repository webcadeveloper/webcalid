import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        database=os.environ.get('PGDATABASE', 'postgres'),
        user=os.environ.get('PGUSER', 'postgres'),
        password=os.environ.get('PGPASSWORD', 'postgres'),
        port=os.environ.get('PGPORT', '5432')
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            is_supervisor BOOLEAN DEFAULT FALSE,
            role VARCHAR(50) DEFAULT 'user',
            pdl_api_key VARCHAR(100),
            ssid VARCHAR(100),
            display_name VARCHAR(100)
        );
    """)

    # Search history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            search_number VARCHAR(50) NOT NULL,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result_found BOOLEAN DEFAULT FALSE,
            source_results JSONB DEFAULT '{}'::jsonb
        );
    """)

    # Phone calls table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS phone_calls (
            id SERIAL PRIMARY KEY,
            search_id INTEGER REFERENCES search_history(id),
            phone_number VARCHAR(20) NOT NULL,
            call_status VARCHAR(20) DEFAULT 'initiated',
            call_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            call_duration INTEGER,
            call_notes TEXT
        );
    """)

    # Verification forms table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verification_forms (
            id SERIAL PRIMARY KEY,
            search_id INTEGER REFERENCES search_history(id),
            verified_by INTEGER REFERENCES users(id),
            form_data JSONB,
            status VARCHAR(20) DEFAULT 'submitted',
            verification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );
    """)

    # Add role column if not exists
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT column_name FROM information_schema.columns 
                          WHERE table_name='users' AND column_name='role') THEN
                ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user';
                ALTER TABLE users ADD CONSTRAINT valid_role 
                    CHECK (role IN ('admin', 'supervisor', 'agent', 'user'));
            END IF;
        END $$;
    """)

    conn.commit()
    cur.close()
    conn.close()

def add_search_history(user_id, search_number, result_found, source_results=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO search_history (user_id, search_number, result_found, source_results) VALUES (%s, %s, %s, %s::jsonb)",
        (user_id, search_number, result_found, json.dumps(source_results or {}))
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

def add_phone_call(user_id, phone_number, status="initiated", duration=None, notes=None, recording_url=None, call_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if call_id:
            # Update existing call
            cur.execute("""
                UPDATE phone_calls 
                SET call_status = %s, call_duration = %s, call_notes = %s, recording_url = %s
                WHERE id = %s
                RETURNING id
            """, (status, duration, notes, recording_url, call_id))
        else:
            # Insert new call
            cur.execute("""
                INSERT INTO phone_calls 
                (user_id, phone_number, call_status, call_duration, call_notes, recording_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, phone_number, status, duration, notes, recording_url))
        result = cur.fetchone()
        if result is None:
            raise Exception("Failed to create or update call record")
        call_id = result[0]
        conn.commit()
        return call_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_phone_calls(user_id=None, search_id=None):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if user_id:
        cur.execute("SELECT * FROM phone_calls WHERE user_id = %s ORDER BY call_date DESC", (user_id,))
    elif search_id:
        cur.execute("SELECT * FROM phone_calls WHERE search_id = %s ORDER BY call_date DESC", (search_id,))
    else:
        cur.execute("SELECT * FROM phone_calls ORDER BY call_date DESC")
        
    calls = cur.fetchall()
    cur.close()
    conn.close()
    return calls