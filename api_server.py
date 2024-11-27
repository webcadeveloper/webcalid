from flask import Flask, request, jsonify
from functools import wraps
import logging
from database import get_db_connection
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS with specific origins
ALLOWED_ORIGINS = [
    "http://0.0.0.0:8502",
    "http://localhost:8502",
    "https://*.repl.co"
]

from flask_cors import CORS
CORS(app, resources={
    r"/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth:
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def verify_user_credentials(username, password):
    """Verify user credentials against database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM users 
            WHERE username = %s
        """, (username,))
        
        result = cur.fetchone()
        if result:
            # In a real application, verify password hash
            return True
        return False
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def authenticate():
    return jsonify({
        'error': 'Authentication required'
    }), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}

# Root endpoint with API information
@app.route('/')
def root():
    return jsonify({
        'name': 'Dashboard Intelligence API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'API information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check endpoint'},
            {'path': '/api/cases', 'method': 'POST', 'description': 'Create new case'}
        ]
    }), 200

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        conn = get_db_connection()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500

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
    try:
        logger.info("Starting API server on port 3000...")
        app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        raise
