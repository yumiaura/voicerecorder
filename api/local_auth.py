#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local username/password and JWT (HS256) for API and stream query `access_token`."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# Local imports
import config

logger = logging.getLogger(__name__)

JWT_ALG = "HS256"


def check_password(username: str, password: str) -> bool:
    """True if env credentials match (constant-time for password)."""
    if username != config.AUTH_USERNAME:
        return False
    a = password.encode("utf-8")
    b = config.AUTH_PASSWORD.encode("utf-8")
    if len(a) != len(b):
        return False
    return bool(secrets.compare_digest(a, b))


def issue_access_token() -> str:
    """New JWT signed with config.SECRET_KEY."""
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(hours=config.AUTH_JWT_HOURS)
    payload: Dict[str, Any] = {
        "sub": config.AUTH_USERNAME,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "typ": "access",
    }
    out = jwt.encode(
        payload,
        config.SECRET_KEY,
        algorithm=JWT_ALG,
    )
    if isinstance(out, bytes):
        return out.decode("ascii")
    return out


def parse_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(  # type: ignore[no-any-return]
            token,
            config.SECRET_KEY,
            algorithms=[JWT_ALG],
        )
    except Exception as e:  # noqa: BLE001
        logger.debug("JWT: %s: %s", type(e).__name__, str(e))
        return None


def get_token_from_flask_request(request) -> Optional[str]:
    """Bearer header or `access_token` query (for <audio> src)."""
    auth = request.headers.get("Authorization", "") or ""
    if auth.startswith("Bearer "):
        return (auth[7:].strip() or None)  # type: ignore[return-value]
    q = request.args.get("access_token")
    if q:
        return str(q)
    return None


def token_ok(request) -> bool:
    raw = get_token_from_flask_request(request)
    if not raw:
        return False
    return bool(parse_token(raw))
