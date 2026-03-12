"""
Authentication routes for user registration and login
Handles user registration, login, and OTP verification
"""

from flask import Blueprint, request, jsonify
from models import db, User
from datetime import datetime, timezone
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Store OTP temporarily (in production, use Redis or database)
otp_storage = {}


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user with password
    Expected JSON:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "password": "user_password"
    }
    """
    try:
        import re
        
        data = request.get_json()
        
        # Validation
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '').strip()
        
        # Check required fields
        if not name or not email or not phone or not password:
            return jsonify({
                'success': False,
                'message': 'Name, email, phone, and password are required'
            }), 400
        
        # List of blocked fake/dummy email domains
        BLOCKED_DOMAINS = [
            'test.com', 'test.co', 'test.org', 'test.net', 'test.io',
            'abc.com', 'example.com', 'placeholder.com', 'temp.com', 'temporary.com',
            'fake.com', 'dummy.com', '123.com', 'aaa.com', 'aaaa.com',
            'mail.tm', '10minutemail.com', 'tempmail.com', 'guerrillamail.com',
            'maildrop.cc', 'mailinator.com', 'emaildrop.com', 'temp-mail.org',
            'throwaway.email', 'yopmail.com', 'sharklasers.com'
        ]
        
        # Validate email format with proper regex (RFC 5322 simplified)
        email_regex = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format. Please use a valid email address.'
            }), 400
        
        # Check for dummy email patterns
        local_part, domain = email.rsplit('@', 1)
        
        # Check minimum length
        if len(local_part) < 2 or len(domain) < 5:
            return jsonify({
                'success': False,
                'message': 'Email address format is invalid. Please use a valid email.'
            }), 400
        
        # Check if using blocked dummy domain
        if domain in BLOCKED_DOMAINS or any(domain.endswith('.' + d) for d in BLOCKED_DOMAINS):
            return jsonify({
                'success': False,
                'message': 'This email domain is not allowed. Please use a real email address from your email provider.'
            }), 400
        
        # Block obvious patterns like user@user.com
        domain_name = domain.replace('.com', '').replace('.co', '').replace('.org', '').replace('.net', '').replace('.io', '')
        if domain_name.lower() == local_part.lower():
            return jsonify({
                'success': False,
                'message': 'Invalid email pattern. Please use a real email address.'
            }), 400
        
        # Block obviously fake patterns
        fake_patterns = ['test', 'abc', 'demo', 'sample', 'temp', 'fake', 'dummy', 'aaa', 'zzz', '123', '000']
        if any(local_part.lower().startswith(p) for p in fake_patterns):
            return jsonify({
                'success': False,
                'message': 'Invalid email pattern. Please use a real email address.'
            }), 400
        
        # Validate phone format (basic check)
        if not phone.isdigit() or len(phone) < 10:
            return jsonify({
                'success': False,
                'message': 'Invalid phone number format'
            }), 400
        
        # Validate password length
        if len(password) < 6:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 409
        
        # Create new user
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            is_verified=True,
            verified_at=datetime.now(timezone.utc)
        )
        
        # Set password (now required)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Generate token
            token = new_user.generate_token()
            
            logger.info(f'New user registered and auto-verified: {email}')
            
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user': new_user.to_dict(),
                'token': token
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error registering user {email}: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Error registering user'
            }), 500
    
    except Exception as e:
        logger.error(f'Error in register endpoint: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error during registration'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user with email and password
    Expected JSON:
    {
        "email": "john@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Check password
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        # Generate token
        token = user.generate_token()
        
        logger.info(f'User logged in: {email}')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
    
    except Exception as e:
        logger.error(f'Error in login endpoint: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error during login'
        }), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify user email with OTP
    Expected JSON:
    {
        "email": "john@example.com",
        "otp": "123456"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({
                'success': False,
                'message': 'Email and OTP are required'
            }), 400
        
        # Check if OTP matches (from email_routes.py)
        if email not in otp_storage:
            return jsonify({
                'success': False,
                'message': 'OTP not found or expired'
            }), 400
        
        stored_otp, expiry = otp_storage[email]
        
        if datetime.now(timezone.utc) > expiry:
            del otp_storage[email]
            return jsonify({
                'success': False,
                'message': 'OTP has expired'
            }), 400
        
        if str(stored_otp) != str(otp):
            return jsonify({
                'success': False,
                'message': 'Invalid OTP'
            }), 400
        
        # Find and verify user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Mark as verified
        user.is_verified = True
        user.verified_at = datetime.now(timezone.utc)
        db.session.commit()
        
        # Clear OTP
        del otp_storage[email]
        
        logger.info(f'User verified: {email}')
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully',
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'Error in verify_email endpoint: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error during verification'
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details by ID"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching user {user_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error fetching user'
        }), 500


@auth_bp.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id: int):
    """Update user profile with address, city, state"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Update allowed fields with proper validation
        try:
            if 'name' in data and data['name']:
                user.name = data['name'].strip()
            
            if 'phone' in data and data['phone']:
                user.phone = data['phone'].strip()
            
            if 'address' in data:
                user.address = data['address'].strip() if data.get('address') else None
            
            if 'city' in data:
                user.city = data['city'].strip() if data.get('city') else None
            
            if 'state' in data:
                user.state = data['state'].strip() if data.get('state') else None
            
            if 'password' in data and data['password']:
                user.set_password(data['password'])
            
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f'User updated: {user.email}')
            
            return jsonify({
                'success': True,
                'message': 'User updated successfully',
                'user': user.to_dict()
            }), 200
        
        except Exception as update_error:
            db.session.rollback()
            logger.error(f'Error during user update for {user_id}: {str(update_error)}')
            raise update_error
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating user {user_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Server error updating user: {str(e)}'
        }), 500


@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """Health check for auth service"""
    return jsonify({
        'status': 'Auth service running',
        'database': 'Connected' if check_database() else 'Not connected'
    }), 200


def check_database():
    """Simple database connectivity check"""
    try:
        db.session.execute('SELECT 1')
        return True
    except:
        return False
