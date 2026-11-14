"""Rate limiting for the authentication endpoints.

Two independent limits on login, so one bad actor cannot lock out a real user, and one
IP cannot brute-force many accounts:

- **per email**: tight (protects one account from credential stuffing).
- **per IP**: looser (protects against one IP guessing across many accounts).

Both count every attempt (successful or not); limits are fixed in code, not read from
the environment, so they cannot be loosened or disabled by a misconfigured deploy.
Registration gets its own, longer-window, per-IP limit to slow automated sign-ups
without blocking a real person who mistypes a field once or twice.
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.core.rate_limit import RateLimiter

MINUTE = 60

# 5 attempts per email per 15 minutes, 20 attempts per IP per 15 minutes.
LOGIN_ATTEMPTS_PER_EMAIL = RateLimiter(limit=5, window=15 * MINUTE)
LOGIN_ATTEMPTS_PER_IP = RateLimiter(limit=20, window=15 * MINUTE)
# 5 registrations per IP per hour.
REGISTRATIONS_PER_IP = RateLimiter(limit=5, window=60 * MINUTE)

ALL_LIMITERS = (LOGIN_ATTEMPTS_PER_EMAIL, LOGIN_ATTEMPTS_PER_IP, REGISTRATIONS_PER_IP)


def client_ip(request: Request) -> str:
    """The caller's address.

    In production, uvicorn is started with `--proxy-headers --forwarded-allow-ips`
    (see scripts/start.sh), so it resolves `request.client` from `X-Forwarded-For`
    for requests coming through Render's trusted proxy. Outside that proxy the header
    is not trusted, so this never reads it directly.
    """
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request, form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> None:
    LOGIN_ATTEMPTS_PER_IP.hit(client_ip(request))
    LOGIN_ATTEMPTS_PER_EMAIL.hit(form.username.strip().lower())


def rate_limit_register(request: Request) -> None:
    REGISTRATIONS_PER_IP.hit(client_ip(request))
