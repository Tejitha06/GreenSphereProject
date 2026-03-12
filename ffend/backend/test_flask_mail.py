#!/usr/bin/env python3
"""Test Flask-Mail integration"""

import os
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail, Message

load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure Flask-Mail (same as app.py)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@greensphere.com')

print('=== FLASK-MAIL CONFIGURATION ===')
print(f'MAIL_SERVER: {app.config["MAIL_SERVER"]}')
print(f'MAIL_PORT: {app.config["MAIL_PORT"]}')
print(f'MAIL_USE_TLS: {app.config["MAIL_USE_TLS"]}')
print(f'MAIL_USERNAME: {app.config["MAIL_USERNAME"]}')
print(f'MAIL_DEFAULT_SENDER: {app.config["MAIL_DEFAULT_SENDER"]}')

# Initialize Flask-Mail
mail = Mail(app)

print('\n=== TESTING FLASK-MAIL ===')

with app.app_context():
    try:
        # Create test message
        test_email = 'test@greensphere.local'  # Send to a test address
        msg = Message(
            subject='GreenSphere - Test Email',
            recipients=[test_email],
            html='<h1>Test OTP: 123456</h1>'
        )
        
        print(f'📧 Attempting to send test email to {test_email}...')
        mail.send(msg)
        print('✅ Flask-Mail TEST PASSED - Email sent successfully!')
        
    except Exception as e:
        print(f'❌ Flask-Mail ERROR: {str(e)}')
        print(f'   Error type: {type(e).__name__}')
        import traceback
        traceback.print_exc()
