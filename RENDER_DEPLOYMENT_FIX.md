# Render Deployment Fix Guide

## Problem

Render is failing to deploy because:
1. Git clone errors from GitHub (possibly due to large files or network issues)
2. Build configuration looking for wrong directory structure (`/src/backend` instead of `/backend`)
3. No explicit build configuration for monorepo

## Solution

### Step 1: Clear Render Cache and Fix Configuration

1. **In Render Dashboard** (https://dashboard.render.com/):
   - Select your backend service
   - Go to **Settings** → **Environment** → scroll to bottom
   - Click **"Clear build cache"**

2. **Update render.yaml** 
   - New file `render.yaml` has been created at repo root
   - Specifies correct paths: `/backend` directory
   - Defines build and start commands

### Step 2: Commit & Push to GitHub

```bash
# Make sure you're in the repo root
cd c:\Users\joshi\OneDrive\Desktop\Search_Engine\Search_Engine

# Add all new files
git add render.yaml build.sh backend/.env.example backend/requirements.txt

# Commit
git commit -m "Add Render configuration and Google OAuth setup"

# Push to GitHub
git push origin main
```

If you get GitHub errors:
- Wait 5 minutes (GitHub might be having temporary issues)
- Try again: `git push origin main`

### Step 3: Redeploy on Render

**Option A: Manual Redeploy** (Recommended)
1. In Render Dashboard, select backend service
2. Go to **Deployments** tab
3. Click **"Manual Deploy"** button
4. Select **Deploy latest commit**

**Option B: Auto-redeploy**
- Disconnect and reconnect GitHub (Settings → GitHub → Disconnect → Reconnect)
- This will trigger a fresh deploy

### Step 4: Verify Deployment

After deploying, check:

1. **Build logs** (Deployments tab):
   - Should say:
     ```
     ==> Installing backend dependencies...
     Successfully installed ...
     ==> Starting web service
     ```

2. **Service status** should be **"Live"** (green)

3. **Test backend**:
   ```bash
   curl https://stock-engine-c1py.onrender.com/api/health
   
   # Should return: {"status": "ok", "message": "Service is running"}
   ```

4. **Test auth**:
   ```bash
   curl -X GET https://stock-engine-c1py.onrender.com/api/auth/check
   
   # Should return: {"logged_in": false, "username": null, "email": null}
   ```

## What Changed

### New Files Created

1. **render.yaml** - Render configuration file
   - Specifies Python 3.11 runtime
   - Sets build command: `cd backend && pip install -r requirements.txt`
   - Sets start command: `cd backend && gunicorn ... api:app`
   - Defines environment variables
   - Specifies root directory as `.` (repo root)

2. **build.sh** - Build script (for reference, Render uses render.yaml)

3. **backend/.env.example** - Environment variables template

### Modified Files

1. **backend/requirements.txt** - Added Google OAuth packages
2. **backend/routes/auth_routes.py** - Added Google OAuth routes
3. **backend/utils/database.py** - Updated schema migration
4. **frontend/src/pages/Login.jsx** - Added Google Sign-in button

## Render Environment Variables

Set these in Render Dashboard (Settings → Environment):

**Required for production:**
```
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://stock-engine-c1py.onrender.com/api/auth/google/callback
FRONTEND_URL=https://stock-engine.vercel.app
FLASK_SECRET_KEY=your_secure_random_key
```

**Get values from:**
- `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` - Google Cloud Console
- `GOOGLE_REDIRECT_URI` - Match your Render backend URL
- `FRONTEND_URL` - Your Vercel frontend URL
- `FLASK_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

## Directory Structure (What Render Expects)

```
search-engine/                  ← Root
  ├── render.yaml              ← Render config
  ├── build.sh                 ← Build script  
  ├── .git/
  ├── .gitignore
  ├── backend/                 ← Backend source
  │   ├── api.py               ← Entry point
  │   ├── app_init.py
  │   ├── requirements.txt
  │   ├── routes/
  │   ├── utils/
  │   └── ...
  └── frontend/                ← Frontend (built separately on Vercel)
      └── ...
```

## Troubleshooting

### Build Fails: "No module named 'google'"

**Cause:** requirements.txt not installed
**Fix:** 
- Check `render.yaml` has correct build command
- Clear cache and redeploy

### Service crashes after deploy

**Cause:** Missing environment variables
**Fix:**
- Set all required env vars in Render dashboard
- Check backend logs for specific error

### GitHub clone fails repeatedly

**Cause:** Large files or network issues
**Fix:**
- Wait 10 minutes and try manual redeploy
- Or push changes again: `git push origin main`

### "Invalid redirect_uri" on OAuth

**Cause:** Redirect URI doesn't match Google Cloud Console
**Fix:**
- Get actual Render URL from dashboard (e.g., `https://stock-engine-c1py.onrender.com`)
- Update `GOOGLE_REDIRECT_URI` to: `https://[YOUR-RENDER-URL]/api/auth/google/callback`
- Update Google Cloud Console OAuth settings with same URL

### Session not persisting across requests

**Cause:** CORS or secure cookies issue
**Fix:** Check `app_init.py` CORS settings match your Vercel domain

## Next: Test Full OAuth Flow

1. Frontend deployed on Vercel ✅
2. Backend deployed on Render (after this fix)
3. Go to `https://stock-engine.vercel.app/login`
4. Click "Sign in with Google"
5. Should see Google OAuth screen
6. Should redirect to `/home` after auth

If it fails, check browser console for errors or Render logs.
