"""
Email routes for OTP and notifications
"""

from flask import Blueprint, request, jsonify
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

email_bp = Blueprint('email', __name__)

# Initialize Flask-Mail (will be configured in app.py)
mail = Mail()


def send_otp_email(email, otp):
    """Send OTP to user's email"""
    try:
        subject = "GreenSphere - Email Verification OTP"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2e7d32;">GreenSphere</h2>
                    <p>Hello,</p>
                    <p>Your One-Time Password (OTP) for email verification is:</p>
                    <div style="background-color: #E8F5E9; border: 2px solid #2e7d32; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #2e7d32; letter-spacing: 5px; margin: 0;">{otp}</h1>
                    </div>
                    <p><strong>This OTP will expire in 10 minutes.</strong></p>
                    <p>Do not share this OTP with anyone. GreenSphere will never ask you for this code.</p>
                    <p>If you didn't request this OTP, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #ccc; margin: 30px 0;">
                    <p style="color: #666; font-size: 12px;">© 2026l GreenSphere. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=body
        )
        
        mail.send(msg)
        logger.info(f"OTP email sent successfully to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False


@email_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """API endpoint to send OTP"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        otp = data.get('otp')
        
        if not email or not otp:
            return jsonify({'success': False, 'message': 'Email and OTP are required'}), 400
        
        if send_otp_email(email, otp):
            return jsonify({
                'success': True,
                'message': f'OTP sent to {email}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_otp endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Server error while sending OTP'
        }), 500


@email_bp.route('/health', methods=['GET'])
def email_health():
    """Check if email service is configured"""
    return jsonify({
        'status': 'Email service running',
        'smtp_server': 'Configured' if os.getenv('MAIL_SERVER') else 'Not configured'
    }), 200
