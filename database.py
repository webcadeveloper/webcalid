import os
import psycopg2
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

def add_search_history(user_id, search_number, result_found):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO search_history (user_id, search_number, result_found) VALUES (%s, %s, %s)",
        (user_id, search_number, result_found)
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
