import os
from flask import Flask, request, jsonify
from functools import wraps
from database import get_db_connection
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_auth(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT password_hash FROM users WHERE username = %s",
            (username,)
        )
        result = cur.fetchone()
        if result:
            # In a real application, verify password hash
            return True
        return False
    finally:
        cur.close()
        conn.close()

def authenticate():
    return jsonify({
        'error': 'Authentication required'
    }), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}

@app.route('/api/cases', methods=['POST'])
@require_auth
def create_case():
    data = request.get_json()
    
    # Required fields validation
    required_fields = ['first_name', 'last_name', 'a_number', 'court_address', 'court_phone']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({
            'error': 'Missing required fields',
            'missing_fields': missing_fields
        }), 400
        
    # A-number validation (9 digits)
    a_number = str(data.get('a_number'))
    if not a_number.isdigit() or len(a_number) != 9:
        return jsonify({
            'error': 'Invalid A-number format. Must be 9 digits.'
        }), 400
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert new case
        cur.execute("""
            INSERT INTO cases (
                first_name, last_name, a_number, court_address, court_phone,
                client_phone, other_client_phone, client_address, client_email,
                created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['first_name'],
            data['last_name'],
            data['a_number'],
            data['court_address'],
            data['court_phone'],
            data.get('client_phone'),
            data.get('other_client_phone'),
            data.get('client_address'),
            data.get('client_email'),
            1  # Default user ID for API calls
        ))
        
        case_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            'message': 'Case created successfully',
            'case_id': case_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating case: {str(e)}")
        return jsonify({
            'error': 'Internal server error'
        }), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
