from flask import jsonify, session
from app_init import app, logger

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
            if 'username' not in session:
                raise APIError('Authentication required', 401)
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator


__all__ = ["APIError", "require_auth"]
