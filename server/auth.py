"""
Аутентификация админки через подписанную cookie (HMAC, stdlib).
"""
from __future__ import annotations
import hashlib
import hmac
import time

import config


def _sign(payload: str) -> str:
    return hmac.new(
        config.ADMIN_PASSWORD.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_session_token() -> str:
    """Создаёт токен сессии: timestamp.signature."""
    ts = str(int(time.time()))
    sig = _sign(ts)
    return f"{ts}.{sig}"


def verify_session_token(token: str) -> bool:
    if not token or "." not in token:
        return False
    ts, sig = token.split(".", 1)
    if not hmac.compare_digest(_sign(ts), sig):
        return False
    try:
        age = int(time.time()) - int(ts)
    except ValueError:
        return False
    return 0 <= age <= config.SESSION_MAX_AGE


def check_password(password: str) -> bool:
    return hmac.compare_digest(password, config.ADMIN_PASSWORD)


def get_session_from_environ(environ) -> str | None:
    cookie = environ.get("HTTP_COOKIE", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith(config.SESSION_COOKIE + "="):
            return part.split("=", 1)[1].strip()
    return None


def is_admin(environ) -> bool:
    token = get_session_from_environ(environ)
    return token is not None and verify_session_token(token)


def session_cookie_header() -> tuple[str, str]:
    token = create_session_token()
    return (
        "Set-Cookie",
        f"{config.SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; "
        f"Max-Age={config.SESSION_MAX_AGE}",
    )


def logout_cookie_header() -> tuple[str, str]:
    return (
        "Set-Cookie",
        f"{config.SESSION_COOKIE}=; Path=/; HttpOnly; Max-Age=0",
    )
