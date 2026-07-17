from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    """Create a signed JWT for the given subject (user id)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.jwt_expiration_hours)
    to_encode = {"sub": subject, "iat": now, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT. Returns the payload or None if invalid/expired."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
