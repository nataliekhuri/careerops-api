"""Password hashing and access tokens."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

ALGORITHM = "HS256"

# Argon2id with the library's recommended parameters.
_password_hash = PasswordHash.recommended()

# Used to spend the same time verifying when an email is unknown, so response
# timing does not reveal which emails are registered.
_DUMMY_HASH = _password_hash.hash("not-a-real-password-just-for-timing")


class TokenError(Exception):
    """The token is missing, invalid, expired or malformed."""


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    if hashed is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False
    return _password_hash.verify(password, hashed)


def _secret() -> str:
    secret = get_settings().jwt_secret_key
    if secret is None:
        raise RuntimeError("JWT_SECRET_KEY is not configured")
    return secret.get_secret_value()


def create_access_token(user_id: int, expires_minutes: int | None = None) -> tuple[str, int]:
    """Return (token, lifetime in seconds) for the given user id."""
    minutes = expires_minutes or get_settings().access_token_expire_minutes
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=minutes), "type": "access"}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM), minutes * 60


def decode_access_token(token: str) -> int:
    """Return the user id in a valid access token, or raise TokenError."""
    try:
        payload = jwt.decode(
            token, _secret(), algorithms=[ALGORITHM], options={"require": ["exp", "iat", "sub", "type"]}
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from None
    if payload.get("type") != "access":
        raise TokenError("not an access token")
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        raise TokenError("invalid subject") from None
