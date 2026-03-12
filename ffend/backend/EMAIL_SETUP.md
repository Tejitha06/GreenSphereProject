# Email OTP Setup Guide

## Overview
The OTP (One-Time Password) system now sends verification codes directly to user email addresses instead of logging to console.

## Backend Configuration

### 1. Install Required Packages
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Email Credentials
Create or update the `.env` file in the backend folder with your email service credentials:

#### For Gmail:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@greensphere.com
```

**Important**: For Gmail, you need to generate an **App Password**, not your regular Gmail password:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification if not already done
3. Go to "App passwords"
4. Select Mail and Windows Computer
5. Copy the generated 16-character password

#### For Other Email Providers:
```env
# Outlook/Office365
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587

# Mailgun
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587

# SendGrid
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
```

### 3. Update Frontend Backend URL (if needed)
In `shared-data.js`, the email endpoint defaults to `http://localhost:5000/api/email/send-otp`

If your backend is on a different URL, update:
```javascript
const response = await fetch('http://your-backend-url:5000/api/email/send-otp', {
```

## How It Works

1. **User Registration**: When a user completes the registration form, they receive an email with a 6-digit OTP
2. **OTP Verification**: User enters the OTP to verify their email address
3. **Account Creation**: Upon successful verification, the account is created

## Testing

### Local Testing with Gmail:
1. Set up your Gmail credentials in `.env`
2. Run the backend: `python run.py`
3. Navigate to registration page in the browser
4. You should receive an email with the OTP

### Preview Email Template
The email is formatted with:
- GreenSphere branding
- Large, easy-to-read OTP code
- 10-minute expiration warning
- Security notice

## Fallback Mechanism
If email sending fails:
- The OTP is logged to the browser console as a fallback
- Users will see a clear error message to try again
- Development/testing can proceed using the console OTP

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "SMTPAuthenticationError" | Check email credentials and App Password (for Gmail) |
| "SMTPNotSupportedError" | Enable "Less secure app access" (Gmail) or use App Password |
| "Connection refused" | Ensure MAIL_SERVER and MAIL_PORT are correct |
| OTP not sent in production | Ensure email service is properly configured on your server |

## Production Deployment
When deploying to production:
1. Use environment variables on your hosting platform (Heroku, AWS, etc.)
2. Never commit credentials to version control
3. Consider using professional email services (SendGrid, Mailgun) for reliability
4. Implement rate limiting on the `/api/email/send-otp` endpoint
5. Add email verification logging for debugging

## Files Modified
- `backend/requirements.txt` - Added Flask-Mail
- `backend/app.py` - Flask-Mail initialization and email blueprint registration
- `backend/routes/email_routes.py` - New email API endpoints
- `shared-data.js` - Updated to call backend email API
