from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, ActivityLog
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def log_activity(user_id, action, description, ip_address=None, user_agent=None):
    """Helper function to log user activities"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            company_name=data.get('company_name', ''),
            phone=data.get('phone', ''),
            country=data.get('country', ''),
            subscription_tier='free'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration activity
        log_activity(
            user.id, 
            'user_registration', 
            f'User {user.username} registered successfully',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            # Log failed login attempt
            log_activity(
                None,
                'login_failed',
                f'Failed login attempt for username: {data["username"]}',
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create session
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        
        # Log successful login
        log_activity(
            user.id,
            'login_success',
            f'User {user.username} logged in successfully',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        user_id = session.get('user_id')
        username = session.get('username')
        
        if user_id:
            # Log logout activity
            log_activity(
                user_id,
                'logout',
                f'User {username} logged out',
                request.remote_addr,
                request.headers.get('User-Agent')
            )
        
        # Clear session
        session.clear()
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'company_name', 'phone', 'country']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Validate email if provided
        if 'email' in data:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'error': 'Email already exists'}), 400
            
            user.email = data['email']
        
        db.session.commit()
        
        # Log profile update
        log_activity(
            user_id,
            'profile_update',
            f'User {user.username} updated profile',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        # Log password change
        log_activity(
            user_id,
            'password_change',
            f'User {user.username} changed password',
            request.remote_addr,
            request.headers.get('User-Agent')
        )
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to change password: {str(e)}'}), 500

@auth_bp.route('/session', methods=['GET'])
def check_session():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'authenticated': False}), 200
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            session.clear()
            return jsonify({'authenticated': False}), 200
        
        return jsonify({
            'authenticated': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to check session: {str(e)}'}), 500

