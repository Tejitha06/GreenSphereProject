"""
Debug script to test login functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app('development')

# Test login route
with app.app_context():
    from models import db, User
    from datetime import datetime, timezone
    
    # Check if test user exists
    test_user = User.query.filter_by(email='test@example.com').first()
    if test_user:
        print(f"Test user found: {test_user.email}")
    else:
        print("Test user not found, creating one...")
        test_user = User(
            name='Test User',
            email='test@example.com',
            phone='1234567890'
        )
        test_user.set_password('password123')
        db.session.add(test_user)
        db.session.commit()
        print(f"Created test user: {test_user.email}")
    
    # Try to authenticate
    try:
        if test_user.check_password('password123'):
            print("Password check passed!")
            token = test_user.generate_token()
            user_dict = test_user.to_dict()
            print(f"Token: {token}")
            print(f"User dict: {user_dict}")
        else:
            print("Password check failed!")
    except Exception as e:
        print(f"Error during authentication: {e}")
        import traceback
        traceback.print_exc()
