# Database Integration Quick Reference

## What's New

### ✅ Database Support Added
- SQLAlchemy ORM integrated
- SQLite for development (default)
- PostgreSQL/MySQL support for production
- User table with authentication fields

### ✅ Backend API Endpoints
```
POST   /api/auth/register        - Register new user
POST   /api/auth/login           - Login user
POST   /api/auth/verify-email    - Verify email with OTP
GET    /api/auth/user/<id>       - Get user details
PUT    /api/auth/user/<id>       - Update user profile
GET    /api/auth/health          - Check auth service
```

### ✅ Security Features
- Password hashing with bcrypt
- JWT token generation
- Email uniqueness validation
- Email verification tracking

### ✅ Frontend Updates
- Registration form sends data to `/api/auth/register`
- Login form sends credentials to `/api/auth/login`
- User data stored in database instead of just localStorage

## Installation Steps

### 1. Install Requirements
```bash
cd ffend/backend
pip install -r requirements.txt
```

### 2. Start Backend
```bash
python run.py
```

Database file `greensphere.db` will be created automatically in the backend directory.

### 3. Test with Frontend
Open registration.html or l1.html to test registration and login.

## Database Location
- **File**: `ffend/backend/greensphere.db`
- **Type**: SQLite (can change via DATABASE_URL in .env)

## Files Changed

### New Files
- `ffend/backend/models.py` - User model definition
- `ffend/backend/routes/auth_routes.py` - Auth endpoints
- `ffend/DATABASE_SETUP.md` - Full documentation

### Modified Files
- `ffend/backend/app.py` - SQLAlchemy initialization
- `ffend/backend/requirements.txt` - Added packages
- `ffend/backend/.env` - Added DATABASE_URL
- `ffend/registration.html` - API integration
- `ffend/l1.html` - API integration

## Key Features

### Registration Flow
1. User fills registration form
2. Data sent to `/api/auth/register`
3. User stored in database
4. User redirected to OTP verification

### Login Flow
1. User enters email and password
2. Credentials verified against database
3. JWT token generated
4. User logged in and redirected to dashboard

### User Data Fields
```
- ID (auto-generated)
- Name
- Email (unique)
- Phone
- Password (hashed)
- Verified Status
- Timestamps (created, updated, last_login)
```

## Production Setup

### Switch to PostgreSQL
1. Install PostgreSQL
2. Create database: `createdb greensphere`
3. Update .env: `DATABASE_URL=postgresql://user:password@localhost/greensphere`
4. Restart backend

### Switch to MySQL
1. Install MySQL
2. Create database with MySQL CLI
3. Update .env: `DATABASE_URL=mysql+pymysql://user:password@localhost/greensphere`
4. Restart backend

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named 'models'" | Ensure models.py is in backend/ directory |
| "CORS error" | Check CORS_ALLOWED_ORIGINS in .env |
| "Database locked" | Restart the backend application |
| "Connection refused" | Ensure backend is running on port 5000 |

## Next Features to Add

- [ ] Password reset functionality
- [ ] Email verification with OTP
- [ ] User profile completion
- [ ] Social login (Google/GitHub)
- [ ] Two-factor authentication
- [ ] Rate limiting on auth endpoints
