import os
import datetime
from typing import Dict, Any

import jwt


# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or os.environ.get(
    "FLASK_SECRET_KEY", "supersecretkey_change_in_production"
)
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = int(os.environ.get("JWT_EXP_SECONDS", 60 * 60 * 24 * 7))  # 7 days


def create_jwt(payload: Dict[str, Any]) -> str:
    """
    Create a signed JWT for the given payload.
    The payload should NOT contain iat/exp; they will be added here.
    """
    now = datetime.datetime.utcnow()
    full_payload = {
        **payload,
        "iat": now,
        "exp": now + datetime.timedelta(seconds=JWT_EXP_SECONDS),
    }
    token = jwt.encode(full_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT>=2 returns str; older versions may return bytes
    return token.decode("utf-8") if isinstance(token, bytes) else token


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a JWT and return its payload.
    Raises jwt.PyJWTError subclasses on failure.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


__all__ = ["create_jwt", "verify_jwt"]

