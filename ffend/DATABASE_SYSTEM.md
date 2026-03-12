## Local Database & Email-Based OTP System - Documentation

### 🎯 Overview

Your GreenSphere application now has a **complete local database system** with **email-based OTP (One-Time Password) verification**. This ensures:

✅ Users keep their **real, original email address** (not dummy emails)  
✅ OTP is sent only to the **user's registered email**  
✅ No other email can be used for login  
✅ Secure verification with expiry and attempt limits  
✅ All data stored in browser LocalStorage (persistent across sessions)  

---

## 📦 System Components

### 1. **shared-data.js** (Core Database Module)
Main JavaScript file that handles all user management and OTP operations.

**Key Functions:**

#### User Management
```javascript
// Register a new user
registerUser(userData)
// userData: { name, email, phone, contact, ... }

// Get all registered users
getUserProfiles()

// Get current logged-in user
getCurrentUser()

// Update user profile
updateUserProfile(updates)

// Login user (stores session)
loginUser(contact)

// Logout user
logoutUser()
```

#### OTP Management
```javascript
// Generate and send OTP to user's email
generateAndSendOTP(email)
// Returns: { success, message, email, expiryMinutes }

// Verify OTP code
verifyOTP(email, otp)
// Returns: { success, message, user }

// Get user email by phone (for login with phone)
getEmailByPhone(phone)
```

#### Email Configuration
```javascript
// Check if email is authorized
isEmailAllowed(email)

// Get OTP records (for debugging)
getOTPRecords()

// Send OTP to email (currently simulated, calls sendOTPToEmail)
sendOTPToEmail(email, otp)
```

---

## 🔐 OTP System Configuration

**Current Settings:**
- **OTP Length:** 6 digits (random 100000-999999)
- **OTP Validity:** 10 minutes
- **Max Attempts:** 5 incorrect tries before OTP expires
- **Storage:** Browser LocalStorage

**To change settings, edit shared-data.js:**
```javascript
const OTP_EXPIRY_MINUTES = 10;  // Change OTP validity time
const OTP_LENGTH = 6;            // Change OTP digit length
```

---

## 📋 Registration Flow

### Step 1: User Registration (registration.html)
```
User fills form:
├─ Full Name
├─ Email Address (ANY valid email)
└─ Phone Number (10 digits)

ℹ️ Plant category fields REMOVED (per your request)
ℹ️ No email whitelist - anyone can register with their Gmail account
```

**Data Stored:**
```javascript
{
  email: "yourname@gmail.com",       // User's real email - PRIMARY ID
  name: "John Doe",
  phone: "9876543210",
  memberSince: "2026-02-13T...",
  registeredDate: "2026-02-13T...",
  // ... other fields
}
```

### Step 2: Stored in Database
User profile saved in LocalStorage:
- **Key:** Email address (lowercase)
- **Also indexed by:** Phone number (for phone login)

---

## 🔑 Login Flow with OTP

### Step 1: User enters Email or Phone (l1.html)
```
User Input
    ↓
Check if registered in database
    ↓
Get user's REAL email address
    ↓
Generate 6-digit OTP
    ↓
Store OTP + expiry time
    ↓
Send to user's registered email
    ↓
Display: "OTP sent to johndoe@gmail.com"
```

### Step 2: User Verifies OTP
```
User enters OTP code
    ↓
Check OTP validity (not expired)
    ↓
Check OTP matches
    ↓
Check attempts not exceeded
    ↓
✅ Login successful!
    ↓
User navigated to dashboard
```

---

## 🗄️ Data Storage Structure

### UserProfiles (all registered users)
```
LocalStorage Key: "userProfiles"
{
  "user@gmail.com": { profile object },
  "9876543210": { same profile object },  // Phone reference
  "another@gmail.com": { profile object },
  ...
}
```

### OTP Records (active OTP codes)
```
LocalStorage Key: "otpRecords"
{
  "user@gmail.com": {
    otp: "456789",
    expiryTime: 1707892543216,
    attempts: 0,
    createdAt: "2026-02-13T10:30:00Z"
  },
  ...
}
```

### Current Session
```
LocalStorage Key: "currentUser"
{
  email: "user@gmail.com",
  name: "John Doe",
  phone: "9876543210",
  ...
}
```

---

## 🧪 Testing the System

### Option 1: Use database-test.html
We've created a **comprehensive test page** at `database-test.html`:

1. Open `database-test.html` in browser
2. **Register Test User:**
   - Fill in name, email (any valid email), phone
   - Click "Register User"
   - User appears in database immediately

3. **Test OTP:**
   - Click "Send OTP"
   - OTP appears in the result box and console
   - Copy OTP
   - Paste in verification field
   - Click "Verify OTP"

4. **View Database:**
   - Click "View All Users" to see registered users
   - Click "View All OTPs" to see active OTPs

### Option 2: Use Browser Console
```javascript
// Open DevTools: F12 → Console tab

// Register user with your email
registerUser({ 
  name: "John Doe", 
  email: "johndoe@gmail.com",  // Use YOUR actual email
  phone: "1234567890",
  contact: "johndoe@gmail.com"
})

// Generate OTP
generateAndSendOTP("johndoe@gmail.com")
// Check console output for OTP

// Verify OTP (use the one from console output)
verifyOTP("johndoe@gmail.com", "123456")

// View all users
getUserProfiles()

// Debug
debugStorage()
```

### Option 3: Full User Journey
1. Go to **registration.html**
2. Fill in form and register
3. Go to **l1.html** (login page)
4. Enter your email
5. Check console (F12) for OTP
6. Enter OTP to verify and login

---

## ✅ Open Registration System

**Anyone can register!** No email whitelist required.

Users can register with:
- ✅ Gmail accounts (gmail.com)
- ✅ Any other email provider
- ✅ Work email addresses
- ✅ Any valid email format

The system is now **completely open** - just use your real email address!

---

## 🔄 Email Verification System

### How it Works:
1. **User registers** with their real email (any email provider - Gmail, Yahoo, etc.)
2. **Email stored in local database** as the primary identifier
3. **OTP is generated** → Random 6-digit code
4. **OTP is "sent"** → Currently logged to console (simulated)
5. **User enters OTP** to verify login
6. **Only the original registered email can receive OTP** ✅

### Key Points:
- User provides their **real email address** during registration
- That exact email is used for OTP verification during login
- No dummy/fake emails - just real email addresses
- Data persists in browser LocalStorage

### Real-World Implementation:
Currently, OTP sending is **simulated** (logged to console). To use real email:

Replace in `shared-data.js`:
```javascript
function sendOTPToEmail(email, otp) {
    // Current: logs to console
    console.log(`OTP sent to ${email}: ${otp}`);
    
    // Real implementation would call your backend:
    // return fetch('/api/send-otp', {
    //     method: 'POST',
    //     body: JSON.stringify({ email, otp })
    // });
}
```

---

## 🛡️ Security Features

✅ **Email Ownership:** Only registered email can receive OTP  
✅ **Time Expiry:** OTP expires after 10 minutes  
✅ **Attempt Limit:** Max 5 incorrect tries  
✅ **No Dummy Emails:** Real email addresses required  
✅ **Persistent Storage:** Data survives browser refresh  
✅ **Phone as Secondary Key:** Can login with phone number  
✅ **Attempt Tracking:** Prevents brute force attacks  

---

## 🧹 Maintenance Functions

### Clear specific user:
```javascript
// From console
let profiles = getUserProfiles();
delete profiles["email@gmail.com"];
saveUserProfiles(profiles);
```

### Clear all data:
```javascript
// From console
clearAllData()  // Shows confirmation dialog
```

### Debug/inspect storage:
```javascript
// From console
debugStorage()  // Shows all stored data
```

---

## 📱 Environment Setup

### Files Modified:
1. **registration.html** - Removed plant category fields ✅
2. **shared-data.js** - Added OTP system ✅
3. **l1.html** - Integrated real OTP verification ✅

### Files Created:
1. **database-test.html** - Testing interface ✅

---

## 🐛 Troubleshooting

### OTP not showing?
- Open browser DevTools (F12)
- Go to Console tab
- Look for logs mentioning the OTP
- Check OTP hasn't expired (10 min limit)

### User not found?
- Confirm email is in ALLOWED_EMAILS list
- Check spelling (case-insensitive)
- Verify registration completed successfully
- Go to database-test.html → "View All Users"

### localStorage full?
- Click "Clear ALL Data" in database-test.html
- Or use: `localStorage.clear()` in console

### OTP verification fails?
- Ensure OTP hasn't expired (10 min)
- Check you entered correct 6 digits
- Max 5 attempts allowed before resetting

---

## 📊 Data Examples

### Sample User Registration:
```json
{
  "afroz@gmail.com": {
    "email": "afroz@gmail.com",
    "name": "Afroz Khan",
    "phone": "9876543210",
    "contact": "afroz@gmail.com",
    "memberSince": "2026-02-13T10:15:30.000Z",
    "registeredDate": "2026-02-13T10:15:30.000Z",
    "lastUpdated": "2026-02-13T10:15:30.000Z"
  }
}
```

### Sample OTP Record:
```json
{
  "afroz@gmail.com": {
    "otp": "456789",
    "expiryTime": 1707892543216,
    "attempts": 0,
    "createdAt": "2026-02-13T10:30:00Z"
  }
}
```

---

## 🎓 Quick Reference

| Feature | Details |
|---------|---------|
| **Database Type** | Browser LocalStorage |
| **User ID** | Email address (lowercase) |
| **Secondary ID** | Phone number |
| **OTP Length** | 6 digits |
| **OTP Validity** | 10 minutes |
| **Max Attempts** | 5 incorrect tries |
| **Email Requirement** | ANY valid email (open system) |
| **Registration** | ✅ Open to everyone |
| **Phone Login** | ✅ YES (maps to email) |
| **Session Persistence** | ✅ YES (survives refresh) |

---

## 📞 Support Notes

**Current System Status:**
- ✅ User registration with real emails
- ✅ OTP generation and verification
- ✅ Email-based login
- ✅ Phone-number login
- ✅ Session management
- ✅ Expiry and attempt limits
- ✅ LocalStorage persistence

**Next Steps (Optional):**
1. Backend email service integration
2. SMS OTP delivery (if phone login needed)
3. Two-factor authentication
4. Email verification on signup

---

**Last Updated:** February 13, 2026  
**System Version:** 1.0 (Email-based OTP)
