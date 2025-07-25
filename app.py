from flask import Flask, request, jsonify, make_response, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
import re
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Validation functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    return True, ""

def validate_name(name):
    """Validate name"""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    return True, ""

# Error handlers
@app.errorhandler(BadRequest)
def handle_bad_request(error):
    return jsonify({'error': str(error)}), 400

@app.errorhandler(NotFound)
def handle_not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(Unauthorized)
def handle_unauthorized(error):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(Exception)
def handle_generic_error(error):
    logger.error(f"Unexpected error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api')
def api_info():
    return jsonify({
        'message': 'User Management System API',
        'version': '1.0.0',
        'endpoints': {
            'GET /users': 'Get all users',
            'GET /user/<id>': 'Get specific user',
            'POST /users': 'Create new user',
            'PUT /user/<id>': 'Update user',
            'DELETE /user/<id>': 'Delete user',
            'GET /search?name=<name>': 'Search users by name',
            'POST /login': 'User login'
        }
    })

@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users],
            'count': len(users)
        })
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise NotFound(f"User with ID {user_id} not found")
        
        return jsonify(user.to_dict())
    except NotFound:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        if not request.is_json:
            raise BadRequest("Content-Type must be application/json")
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")
    
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
    
        # Validate inputs
        name_valid, name_error = validate_name(name)
        if not name_valid:
            raise BadRequest(name_error)
        
        if not validate_email(email):
            raise BadRequest("Invalid email format")
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            raise BadRequest(password_error)
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            raise BadRequest("Email already registered")
        
        # Create user
        password_hash = generate_password_hash(password)
        new_user = User(name=name, email=email, password_hash=password_hash)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"User created successfully: {email}")
        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201
        
    except (BadRequest, ValueError) as e:
        db.session.rollback()
        raise BadRequest(str(e))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    try:
        if not request.is_json:
            raise BadRequest("Content-Type must be application/json")
        
        user = User.query.get(user_id)
        if not user:
            raise NotFound(f"User with ID {user_id} not found")
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            name = data['name'].strip()
            name_valid, name_error = validate_name(name)
            if not name_valid:
                raise BadRequest(name_error)
            user.name = name
        
        if 'email' in data:
            email = data['email'].strip().lower()
            if not validate_email(email):
                raise BadRequest("Invalid email format")
            
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user_id:
                raise BadRequest("Email already registered")
            
            user.email = email
        
        if 'password' in data:
            password = data['password']
            password_valid, password_error = validate_password(password)
            if not password_valid:
                raise BadRequest(password_error)
            user.password_hash = generate_password_hash(password)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"User {user_id} updated successfully")
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        })
        
    except (BadRequest, NotFound) as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise

@app.route('/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise NotFound(f"User with ID {user_id} not found")
        
        db.session.delete(user)
        db.session.commit()
        
        logger.info(f"User {user_id} deleted successfully")
        return jsonify({'message': 'User deleted successfully'})
        
    except NotFound:
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise

@app.route('/search', methods=['GET'])
def search_users():
    """Search users by name"""
    try:
        name = request.args.get('name', '').strip()
    
        if not name:
            raise BadRequest("Please provide a name parameter to search")
        
        if len(name) < 2:
            raise BadRequest("Search term must be at least 2 characters long")
        
        users = User.query.filter(User.name.ilike(f'%{name}%')).all()
        
        return jsonify({
            'users': [user.to_dict() for user in users],
            'count': len(users),
            'search_term': name
        })
        
    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise

@app.route('/login', methods=['POST'])
def login():
    """User login"""
    try:
        if not request.is_json:
            raise BadRequest("Content-Type must be application/json")
        
        data = request.get_json()
        
        if 'email' not in data or 'password' not in data:
            raise BadRequest("Email and password are required")
        
        email = data['email'].strip().lower()
        password = data['password']
    
        if not validate_email(email):
            raise BadRequest("Invalid email format")
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            raise Unauthorized("Invalid email or password")
        
        logger.info(f"User {user.id} logged in successfully")
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        })
        
    except (BadRequest, Unauthorized):
        raise
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5009, debug=True)