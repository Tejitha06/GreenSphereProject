#!/usr/bin/env python3
"""Test SMTP connection and email configuration"""

import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

print('=== EMAIL CONFIGURATION CHECK ===')
print(f'MAIL_SERVER: {os.getenv("MAIL_SERVER")}')
print(f'MAIL_PORT: {os.getenv("MAIL_PORT")}')
print(f'MAIL_USE_TLS: {os.getenv("MAIL_USE_TLS")}')
print(f'MAIL_USERNAME: {os.getenv("MAIL_USERNAME")}')
password = os.getenv("MAIL_PASSWORD")
if password:
    print(f'MAIL_PASSWORD: {password[:3]}***')
else:
    print('MAIL_PASSWORD: NOT SET - ❌ CRITICAL ERROR')
print(f'MAIL_DEFAULT_SENDER: {os.getenv("MAIL_DEFAULT_SENDER")}')

print('\n=== TESTING SMTP CONNECTION ===')
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    print('✅ Connected to SMTP server')
    server.starttls()
    print('✅ TLS enabled')
    
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    if not username:
        print('❌ ERROR: MAIL_USERNAME not set in .env')
        exit(1)
    
    if not password:
        print('❌ ERROR: MAIL_PASSWORD not set in .env')
        exit(1)
    
    server.login(username, password)
    print(f'✅ Login successful with {username}')
    server.quit()
    print('✅ SMTP TEST PASSED - Credentials are valid!')
    
except smtplib.SMTPAuthenticationError as e:
    print(f'❌ AUTHENTICATION ERROR: {str(e)}')
    print('   - Invalid username or password')
    print('   - Check if app password is correct')
    print('   - Make sure 2-Step Verification is enabled')
    
except smtplib.SMTPException as e:
    print(f'❌ SMTP ERROR: {str(e)}')
    
except Exception as e:
    print(f'❌ CONNECTION ERROR: {str(e)}')
