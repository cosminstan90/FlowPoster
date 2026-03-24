import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from backend.config import settings

_ALGORITHM = "HS256"


def verify_credentials(username: str, password: str) -> bool:
    return secrets.compare_digest(username, settings.ADMIN_USERNAME) and secrets.compare_digest(
        password, settings.ADMIN_PASSWORD
    )


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
