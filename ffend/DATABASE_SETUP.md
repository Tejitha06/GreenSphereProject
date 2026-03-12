# GreenSphere Database Setup Guide

## Overview
This guide explains the SQL database integration for user registration and login functionality. The system now stores user data in a SQL database instead of just local storage.

## Database Architecture

### Supported Databases
- **SQLite** (default - recommended for development)
- **PostgreSQL** (recommended for production)
- **MySQL** (alternative for production)

### User Table Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    password_hash VARCHAR(255),
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME NULL
);
```

## Setup Instructions

### Step 1: Install Dependencies
```bash
cd ffend/backend
pip install -r requirements.txt
```

New packages added:
- **Flask-SQLAlchemy**: ORM for database management
- **bcrypt**: Password hashing and verification
- **PyJWT**: JWT token generation for session management

### Step 2: Configure Database

#### Option A: SQLite (Recommended for Development)
No additional setup needed! SQLite will be created automatically.

Update `.env` file:
```
DATABASE_URL=sqlite:///greensphere.db
```

#### Option B: PostgreSQL (Production)
Install PostgreSQL and create a database:
```bash
# On Windows with pgAdmin
# On Mac: brew install postgresql
# On Linux: sudo apt-get install postgresql

# Create database
createdb greensphere
```

Update `.env` file:
```
DATABASE_URL=postgresql://username:password@localhost:5432/greensphere
```

#### Option C: MySQL
Install MySQL and create a database:
```bash
# On Windows: Download MySQL installer
# On Mac: brew install mysql
# On Linux: sudo apt-get install mysql-server

# Create database
mysql -u root -p
> CREATE DATABASE greensphere;
> QUIT;
```

Update `.env` file:
```
DATABASE_URL=mysql+pymysql://root:password@localhost/greensphere
```

### Step 3: Start the Backend

```bash
cd ffend/backend
python run.py
```

The application will automatically:
1. Connect to the database
2. Create all necessary tables
3. Initialize the Flask app

You should see in the console:
```
Database tables created
Flask app created with config: development
Running on http://localhost:5000/
```

## API Endpoints

### Authentication Endpoints

#### 1. User Registration
**POST** `/api/auth/register`

Request:
```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "password": "optional_password"  // Optional
}
```

Response (Success):
```json
{
    "success": true,
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "email": "john@example.com",
        "name": "John Doe"
    }
}
```

Response (Error):
```json
{
    "success": false,
    "message": "Email already registered"
}
```

#### 2. User Login
**POST** `/api/auth/login`

Request:
```json
{
    "email": "john@example.com",
    "password": "user_password"
}
```

Response (Success):
```json
{
    "success": true,
    "message": "Login successful",
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "is_verified": false,
        "created_at": "2024-01-15T10:30:00"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Response (Error):
```json
{
    "success": false,
    "message": "Invalid email or password"
}
```

#### 3. Verify Email
**POST** `/api/auth/verify-email`

Request:
```json
{
    "email": "john@example.com",
    "otp": "123456"
}
```

Response (Success):
```json
{
    "success": true,
    "message": "Email verified successfully",
    "user": {
        "id": 1,
        "is_verified": true,
        "verified_at": "2024-01-15T10:35:00"
    }
}
```

#### 4. Get User Details
**GET** `/api/auth/user/<user_id>`

Response:
```json
{
    "success": true,
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "is_verified": true,
        "created_at": "2024-01-15T10:30:00"
    }
}
```

#### 5. Update User Profile
**PUT** `/api/auth/user/<user_id>`

Request:
```json
{
    "name": "Jane Doe",
    "phone": "9876543210",
    "password": "new_password"  // Optional
}
```

Response:
```json
{
    "success": true,
    "message": "User updated successfully",
    "user": {
        "id": 1,
        "name": "Jane Doe",
        "email": "jane@example.com"
    }
}
```

## Frontend Integration

### Registration Page
The registration page now sends data to the backend API:
```javascript
fetch('http://localhost:5000/api/auth/register', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: "User Name",
        email: "user@example.com",
        phone: "1234567890"
    })
})
```

### Login Page
The login page now authenticates against the database:
```javascript
fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: "user@example.com",
        password: "user_password"
    })
})
```

## Features Implemented

### Security Features
✅ Password hashing with bcrypt
✅ JWT token generation for sessions
✅ Email uniqueness validation
✅ Phone number validation
✅ User verification status tracking

### User Data Stored
- User ID (auto-generated)
- Full Name
- Email (unique)
- Phone Number
- Password Hash (if provided)
- Verification Status
- Registration Date
- Last Login Date
- Updated Date

## Database Files

### Backend Files Added
- `models.py` - SQLAlchemy User model definition
- `routes/auth_routes.py` - Authentication endpoints

### Backend Files Modified
- `app.py` - Added SQLAlchemy initialization and auth blueprint registration
- `config.py` - Already had database configuration (no changes needed)
- `requirements.txt` - Added database packages
- `.env` - Added DATABASE_URL configuration

### Frontend Files Modified
- `registration.html` - Updated to send registration data to backend API
- `l1.html` - Updated to send login credentials to backend API

## Testing

### Test Registration
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","phone":"1234567890"}'
```

### Test Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## Troubleshooting

### Issue: "Module 'models' not found"
**Solution**: Ensure `models.py` is in the `backend` directory and Python path includes the backend folder.

### Issue: "Database locked" (SQLite)
**Solution**: Close all connections and restart the application.

### Issue: "Connection refused" for PostgreSQL/MySQL
**Solution**: 
1. Verify database server is running
2. Check DATABASE_URL in .env file
3. Verify credentials are correct

### Issue: CORS errors on frontend
**Solution**: Verify `CORS_ALLOWED_ORIGINS` in `.env` includes frontend URL.

## Security Recommendations

For Production:
1. Use PostgreSQL or MySQL instead of SQLite
2. Use strong SECRET_KEY in .env
3. Enable HTTPS/SSL
4. Use environment variables for sensitive data
5. Implement rate limiting on login/register endpoints
6. Add CSRF protection
7. Use secure password policies
8. Regular database backups

## Next Steps

1. **Email Verification**: Integrate OTP verification with email sending
2. **Password Reset**: Implement forgot password functionality
3. **User Profiles**: Extend user model with additional fields (address, city, state, etc.)
4. **Social Login**: Add Google/GitHub OAuth integration
5. **Two-Factor Authentication**: Implement 2FA for enhanced security

## File Structure
```
ffend/
├── backend/
│   ├── models.py                 # NEW: User database model
│   ├── routes/
│   │   ├── auth_routes.py        # NEW: Auth endpoints
│   │   └── ...other routes
│   ├── app.py                    # MODIFIED: Add SQLAlchemy
│   ├── config.py                 # Database config already included
│   ├── requirements.txt           # MODIFIED: Add new packages
│   ├── .env                      # MODIFIED: Add DATABASE_URL
│   └── ...other files
├── registration.html             # MODIFIED: Send to backend API
├── l1.html                       # MODIFIED: Send login to API
└── ...other frontend files
```
