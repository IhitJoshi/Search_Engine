# Google OAuth 2.0 Setup Guide

This document explains how to set up Google OAuth for the Stock Search Engine application.

## Overview

The app now supports:
- ✅ Traditional username/password login (unchanged)
- ✅ Google OAuth 2.0 sign-in
- ✅ Seamless account linking (if email matches)

## Backend Setup

### 1. Install Dependencies

Dependencies have been added to `requirements.txt`:
```
google-auth>=2.25.0,<3.0.0
google-auth-oauthlib>=1.1.0,<2.0.0
google-auth-httplib2>=0.2.0,<0.3.0
requests>=2.31.0,<3.0.0
```

Run:
```bash
pip install -r backend/requirements.txt
```

### 2. Get Google OAuth Credentials

Go to [Google Cloud Console](https://console.cloud.google.com/):

1. Create a new project (or use existing)
2. Enable Google+ API
3. Create OAuth 2.0 credentials:
   - Application type: **Web application**
   - Authorized JavaScript origins: Add your domains
     - `https://stock-engine.vercel.app` (production)
     - `http://localhost:5173` (local development)
   - Authorized redirect URIs: Add callback URLs
     - `https://stock-engine-c1py.onrender.com/api/auth/google/callback` (production)
     - `http://localhost:5000/api/auth/google/callback` (local development)

4. Copy the **Client ID** and **Client Secret**

### 3. Set Environment Variables

Add these to your **Render backend** environment variables:

```
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://stock-engine-c1py.onrender.com/api/auth/google/callback
FRONTEND_URL=https://stock-engine.vercel.app
FLASK_SECRET_KEY=your_secret_key (already set)
```

For **local development**, create `backend/.env`:
```
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
FRONTEND_URL=http://localhost:5173
FLASK_SECRET_KEY=dev_secret_key
```

### 4. Database Migration

The database is automatically migrated when the app starts:
- Adds `google_id TEXT UNIQUE` column to users table
- Makes `password_hash` nullable (for OAuth-only users)
- Makes `username` nullable (for OAuth-only users)
- Existing users are NOT affected

## Frontend Setup

### 1. "Sign in with Google" Button

The button is already added to `frontend/src/pages/Login.jsx`:
- Visible below the traditional login form
- Clicking redirects to `/api/auth/google/login`
- Uses Google's official colors and logo

### 2. How It Works

1. User clicks "Sign in with Google"
2. Backend redirects to Google's OAuth consent screen
3. User authorizes the app
4. Google redirects back to `/api/auth/google/callback`
5. Backend:
   - Verifies the ID token
   - Creates or finds user by google_id or email
   - Sets session
   - Redirects to `/home`
6. Frontend's existing auth check works ✅

## API Routes

### New OAuth Routes

**GET `/api/auth/google/login`**
- Redirects user to Google OAuth consent screen
- Scope: `openid email profile`

**GET `/api/auth/google/callback`**
- Handles Google redirect
- Creates/updates user in database
- Sets session
- Redirects to frontend `/home`

### Existing Routes (Unchanged)

- `POST /api/login` - Traditional username/password
- `POST /api/signup` - Traditional email signup
- `GET /api/auth/check` - Check authentication status
- `POST /api/logout` - Logout

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,                 -- NULL for OAuth-only users
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,                   -- NULL for OAuth-only users
    google_id TEXT UNIQUE,                -- NULL for traditional users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Examples

**Traditional user:**
```
id: 1
username: john_doe
email: john@example.com
password_hash: sha256_hash
google_id: NULL
```

**OAuth user:**
```
id: 2
username: NULL
email: jane@example.com
password_hash: NULL
google_id: 117234567890123456789
```

**Linked user (both methods):**
```
id: 3
username: bob_smith
email: bob@example.com
password_hash: sha256_hash
google_id: 117234567890123459999
```

## Testing Locally

### 1. Backend

```bash
cd backend

# Create .env with credentials
export GOOGLE_CLIENT_ID=your_client_id
export GOOGLE_CLIENT_SECRET=your_client_secret
export GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
export FRONTEND_URL=http://localhost:5173
export FLASK_SECRET_KEY=dev_key

# Run Flask
python -m flask run
```

### 2. Frontend

```bash
cd frontend
npm run dev
```

### 3. Test Flow

1. Open `http://localhost:5173/login`
2. Click "Sign in with Google"
3. You should see Google's OAuth screen
4. Authorize the app
5. Should redirect to `/home` and be logged in
6. Check `api/auth/check` returns `logged_in: true`

## Deployment

### Render (Backend)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select your backend service
3. Go to **Environment** tab
4. Add environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
   - `FRONTEND_URL`
5. Manual deploy or push to trigger redeploy

### Vercel (Frontend)

Frontend requires no environment variables (uses relative paths to backend).

## Troubleshooting

### Issue: OAuth button returns to login page

**Cause:** Environment variables not set
**Fix:** Check Render environment variables are saved

### Issue: "Invalid Client" error

**Cause:** Wrong client ID or secret
**Fix:** Copy exact values from Google Cloud Console

### Issue: Redirect URI mismatch

**Cause:** Redirect URI doesn't match Google Cloud Console config
**Fix:** Update both Google Console and environment variables

The redirect URI must be:
- Exactly as registered in Google Console
- HTTPS in production
- Include `/api/auth/google/callback` path

### Issue: Session not persisting

**Cause:** Cross-origin cookies not working
**Fix:** Check CORS configuration in `app_init.py`
- `SESSION_COOKIE_SECURE = True`
- `SESSION_COOKIE_SAMESITE = 'None'`
- Frontend domain in allowed origins

## Code Files Modified

### Backend
- `backend/requirements.txt` - Added Google OAuth packages
- `backend/utils/database.py` - Updated schema migration
- `backend/routes/auth_routes.py` - Added OAuth routes

### Frontend
- `frontend/src/pages/Login.jsx` - Added "Sign in with Google" button

## Security Notes

1. **Never commit secrets** - Use environment variables only
2. **HTTPS required** - OAuth only works over HTTPS (except localhost)
3. **ID token verification** - Google's server verifies the token
4. **Session cookies** - Secure, HttpOnly flags enabled
5. **CORS restricted** - Only approved origins can access API

## Future Enhancements

- Add Google logout (revoke token)
- Link multiple auth methods to one account
- Unlink Google account
- OAuth for signup without email
- GitHub OAuth
- Microsoft OAuth
