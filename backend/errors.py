from flask import jsonify, session, request
from app_init import app, logger
from utils.jwt_utils import verify_jwt
import jwt

class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@app.errorhandler(APIError)
def handle_api_error(error: APIError):
    return jsonify({'error': error.message}), error.status_code


@app.errorhandler(Exception)
def handle_unexpected_error(error: Exception):
    logger.error(f"Unexpected error: {error}")
    return jsonify({'error': 'An unexpected error occurred'}), 500


def require_auth():
    def decorator(f):
        def wrapped(*args, **kwargs):
            # Prefer session-based auth if available (backwards compatible)
            if 'username' not in session:
                # Fallback to JWT-based auth via Authorization: Bearer <token>
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ", 1)[1].strip()
                    try:
                        payload = verify_jwt(token)
                        # Optionally hydrate session for downstream code
                        session['username'] = payload.get("username")
                        session['email'] = payload.get("email")
                    except jwt.ExpiredSignatureError:
                        raise APIError('Session expired. Please log in again.', 401)
                    except jwt.InvalidTokenError:
                        raise APIError('Invalid authentication token.', 401)
                else:
                    raise APIError('Authentication required', 401)
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator


__all__ = ["APIError", "require_auth"]
