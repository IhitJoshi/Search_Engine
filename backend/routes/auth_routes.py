from flask import request, jsonify, redirect, session, url_for
from utils.database import get_connection, hash_password
from app_init import app, logger, FRONTEND_URL
from errors import APIError, require_auth
from utils.jwt_utils import create_jwt
import sqlite3
import os
import requests
from urllib.parse import urlencode, quote
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not all([username, email, password]):
            raise APIError("Missing required fields: username, email, password")

        if len(password) < 6:
            raise APIError("Password must be at least 6 characters long")

        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, hash_password(password))
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "username" in str(e):
                    raise APIError("Username already exists")
                elif "email" in str(e):
                    raise APIError("Email already exists")
                else:
                    raise APIError("User already exists")

        logger.info(f"New user registered: {username}")
        return jsonify({
            'message': 'Registration successful!',
            'username': username
        }), 201

    except APIError:
        raise
    except Exception as e:
        logger.exception("Signup error")
        raise APIError("Registration failed")


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            raise APIError("Username and password required")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, email FROM users WHERE username = ? AND password_hash = ?",
                (username, hash_password(password))
            )
            user = cursor.fetchone()

        if user:
            from flask import session
            session.permanent = True  # Make session persist across browser restarts
            session['username'] = user['username']
            session['email'] = user['email']

            # Issue JWT so frontend can authenticate without relying on cookies
            token = create_jwt({
                "username": user['username'],
                "email": user['email']
            })

            logger.info(f"User logged in: {username}")
            return jsonify({
                'message': 'Login successful!',
                'user': {
                    'username': user['username'],
                    'email': user['email']
                },
                'token': token
            })
        else:
            raise APIError("Invalid credentials", 401)

    except APIError:
        raise
    except Exception as e:
        logger.exception("Login error")
        raise APIError("Login failed")


@app.route("/api/logout", methods=["POST"])
@require_auth()
def logout():
    from flask import session
    username = session.get('username')
    session.clear()
    logger.info(f"User logged out: {username}")
    return jsonify({'message': 'Logout successful!'})


@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")

        email = data.get("email", "").strip()

        if not email:
            raise APIError("Email is required")

        logger.info(f"Password reset requested for email: {email}")
        return jsonify({
            'message': 'If that email exists, password reset instructions have been sent',
            'email': email
        })

    except APIError:
        raise
    except Exception:
        logger.exception("Forgot password error")
        raise APIError("Failed to process password reset request")


@app.route("/api/auth/check", methods=["GET"])
def check_auth():
    """Check if user is authenticated and return user info"""
    try:
        from flask import session, request
        username = session.get('username')
        email = session.get('email')

        # If no session, try JWT from Authorization header
        if not username:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                try:
                    from utils.jwt_utils import verify_jwt
                    import jwt
                    payload = verify_jwt(token)
                    username = payload.get("username")
                    email = payload.get("email")
                except jwt.PyJWTError:
                    username = None
                    email = None

        if username:
            return jsonify({
                'logged_in': True,
                'username': username,
                'email': email
            }), 200
        else:
            return jsonify({
                'logged_in': False,
                'username': None,
                'email': None
            }), 200

    except APIError:
        raise
    except Exception as e:
        logger.exception("Auth check error")
        raise APIError("Failed to check authentication")


@app.route("/api/auth/update-email", methods=["POST"])
@require_auth()
def update_email():
    """Update user's email address"""
    try:
        from flask import session
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")

        new_email = data.get("email", "").strip()

        if not new_email:
            raise APIError("Email is required")

        username = session.get('username')

        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE users SET email = ? WHERE username = ?",
                    (new_email, username)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                raise APIError("Email already exists")

        session['email'] = new_email
        logger.info(f"Email updated for user: {username}")
        return jsonify({
            'message': 'Email updated successfully',
            'email': new_email
        })

    except APIError:
        raise
    except Exception as e:
        logger.exception("Update email error")
        raise APIError("Failed to update email")


@app.route("/api/auth/change-password", methods=["POST"])
@require_auth()
def change_password():
    """Change user's password"""
    try:
        from flask import session
        data = request.get_json()
        if not data:
            raise APIError("No JSON data provided")

        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not current_password or not new_password:
            raise APIError("Current password and new password are required")

        if len(new_password) < 6:
            raise APIError("New password must be at least 6 characters long")

        username = session.get('username')

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()

            if not user:
                raise APIError("User not found", 404)

            # Verify current password
            if user['password_hash'] != hash_password(current_password):
                raise APIError("Current password is incorrect", 401)

            # Update password
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (hash_password(new_password), username)
            )
            conn.commit()

        logger.info(f"Password changed for user: {username}")
        return jsonify({
            'message': 'Password changed successfully'
        })

    except APIError:
        raise
    except Exception as e:
        logger.exception("Change password error")
        raise APIError("Failed to change password")

# ============ GOOGLE OAUTH 2.0 ROUTES ============

@app.route("/api/auth/google/login", methods=["GET"])
def google_login():
    """Redirect to Google OAuth consent screen"""
    try:
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
        
        if not client_id or not redirect_uri:
            raise APIError("Google OAuth not configured", 500)
        
        # Build Google OAuth URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline"
        }
        
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        logger.info("Redirecting user to Google OAuth consent screen")
        
        return redirect(google_auth_url)
    
    except APIError:
        raise
    except Exception as e:
        logger.exception("Google login error")
        raise APIError("Failed to initiate Google OAuth")


@app.route("/api/auth/google/callback", methods=["GET"])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        code = request.args.get("code")
        error = request.args.get("error")
        
        if error:
            logger.warning(f"Google OAuth error: {error}")
            return redirect(f"{FRONTEND_URL}/login?error={error}")
        
        if not code:
            raise APIError("Authorization code not received", 400)
        
        # Exchange code for token
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
        
        if not all([client_id, client_secret, redirect_uri]):
            raise APIError("Google OAuth not properly configured", 500)
        
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            raise Exception("Failed to exchange authorization code")
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        
        if not access_token:
            raise Exception("No access token received")
        
        # Fetch user info from Google
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if userinfo_response.status_code != 200:
            logger.error(f"Failed to fetch Google user info: {userinfo_response.text}")
            raise Exception("Failed to fetch Google user info")
        
        userinfo = userinfo_response.json()
        
        # Extract user info
        google_id = userinfo.get("sub") or userinfo.get("id")
        email = userinfo.get("email")
        name = userinfo.get("name")
        
        if not email:
            raise Exception("Missing required email from Google user info")
        
        logger.info(f"Google OAuth successful for email: {email}")
        
        # Check if user exists
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = {col[1] for col in cursor.fetchall()}
            has_google_id = "google_id" in columns
            has_provider = "provider" in columns
            has_password_hash = "password_hash" in columns
            
            cursor.execute(
                "SELECT id, username, email FROM users WHERE email = ?",
                (email,)
            )
            
            user = cursor.fetchone()
            
            if user:
                # Existing user
                username = user['username'] or email.split('@')[0]
                user_email = user['email']
                logger.info(f"Existing Google user logged in: {email}")
                
                update_fields = []
                params = []
                if has_google_id and google_id:
                    update_fields.append("google_id = ?")
                    params.append(google_id)
                if has_provider:
                    update_fields.append("provider = ?")
                    params.append("google")
                if update_fields:
                    params.append(user_email)
                    cursor.execute(
                        f"UPDATE users SET {', '.join(update_fields)} WHERE email = ?",
                        tuple(params)
                    )
                    conn.commit()
            else:
                # New user - create account
                # Use email local-part as base username to avoid collisions when
                # multiple Google accounts share the same full name.
                base_username = (email.split('@')[0] or "user").strip()
                if not base_username:
                    base_username = "user"

                user_email = email

                columns_to_insert = ["username", "email"]

                # Static columns that don't change across collision retries
                static_columns = []
                static_values = []
                if has_password_hash:
                    static_columns.append("password_hash")
                    static_values.append(None)
                if has_google_id and google_id:
                    static_columns.append("google_id")
                    static_values.append(google_id)
                if has_provider:
                    static_columns.append("provider")
                    static_values.append("google")

                # Try to insert with unique username, appending a numeric suffix on conflict
                suffix = 0
                while True:
                    username = base_username if suffix == 0 else f"{base_username}{suffix}"
                    try:
                        cols = columns_to_insert + static_columns
                        values = [username, user_email] + static_values
                        placeholders = ", ".join(["?"] * len(cols))
                        cursor.execute(
                            f"INSERT INTO users ({', '.join(cols)}) VALUES ({placeholders})",
                            tuple(values)
                        )
                        conn.commit()
                        logger.info(f"New Google user created: {email} with username {username}")
                        break
                    except sqlite3.IntegrityError as e:
                        # Username collision -> try next suffix
                        if "username" in str(e):
                            suffix += 1
                            continue
                        # Any other integrity error is unexpected; re-raise
                        raise
        
        # Set session
        session.permanent = True  # Make session persist across browser restarts
        session['username'] = username
        session['email'] = user_email

        # Issue JWT for frontend (token-based auth independent of cookies)
        token = create_jwt({
            "username": username,
            "email": user_email
        })

        # Redirect to frontend with token & username in query params
        redirect_url = f"{FRONTEND_URL}/home?token={quote(token)}&username={quote(username)}"
        
        logger.info(f"Google OAuth user logged in, redirecting to {redirect_url}")
        return redirect(redirect_url)
    
    except Exception as e:
        logger.exception("Google callback error")
        return redirect(f"{FRONTEND_URL}/login?error=oauth_failed")