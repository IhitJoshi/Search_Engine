from flask import request, jsonify
from utils.database import get_connection, hash_password
from app_init import app, logger
from errors import APIError, require_auth
import sqlite3


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
            session['username'] = user['username']
            session['email'] = user['email']

            logger.info(f"User logged in: {username}")
            return jsonify({
                'message': 'Login successful!',
                'user': {
                    'username': user['username'],
                    'email': user['email']
                }
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
        from flask import session
        username = session.get('username')
        email = session.get('email')

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
