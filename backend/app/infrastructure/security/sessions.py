"""Opaque session/CSRF token generation and hashing.

The raw session token is only ever held by the client's HttpOnly cookie;
only its SHA-256 hash is persisted server-side (see infrastructure/db/models.py
UserSession.token_hash), so a database leak alone cannot be used to hijack
a live session (the attacker would still need the raw cookie value).
"""

from __future__ import annotations

import hashlib
import secrets


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
