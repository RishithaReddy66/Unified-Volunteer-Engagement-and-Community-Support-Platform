import jwt
import os
from datetime import datetime, timedelta, timezone

JWT_SECRET = os.environ.get("JWT_SECRET", "jwt-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", 24))


def generate_token(user_id: str, role: str) -> str:
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
