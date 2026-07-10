"""Column-level encryption at rest for sensitive fields.

Why column-level (application-layer) encryption rather than disk/volume
encryption alone: it protects project/calculation/report data even if a
database backup, dump, or disk snapshot is exfiltrated independently of the
running application, and it works identically in local dev and in any
hosting environment without depending on the host's disk-encryption
configuration. It's self-hosted (no cloud KMS), which matches CLAUDE.md's
privacy-first and low-operating-cost guidance for a small self-hosted
deployment. Disk/volume encryption (e.g. LUKS, or the hosting provider's
encrypted-volume feature) is still recommended as defense-in-depth at
deploy time — this is not a substitute for it, just the layer that protects
against DB-level exposure.

The Fernet key is derived from FIELD_ENCRYPTION_SECRET (see app/config.py)
via SHA-256, so any sufficiently random environment secret works without
needing to be pre-formatted as a Fernet key.
"""

from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator

from app.config import derive_fernet_key, settings

_fernet = Fernet(derive_fernet_key(settings.field_encryption_secret))


class EncryptedString(TypeDecorator):
    """A UTF-8 string, encrypted at rest with Fernet (AES-128-CBC + HMAC)."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        return _fernet.encrypt(value.encode("utf-8"))

    def process_result_value(self, value: bytes | None, dialect: Any) -> str | None:
        if value is None:
            return None
        return _fernet.decrypt(value).decode("utf-8")


class EncryptedBytes(TypeDecorator):
    """Raw binary data (e.g. a generated PDF), encrypted at rest with Fernet."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: bytes | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        return _fernet.encrypt(value)

    def process_result_value(self, value: bytes | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        return _fernet.decrypt(value)


class EncryptedJSON(TypeDecorator):
    """A JSON-serializable value, encrypted at rest with Fernet."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Any | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        return _fernet.encrypt(json.dumps(value).encode("utf-8"))

    def process_result_value(self, value: bytes | None, dialect: Any) -> Any | None:
        if value is None:
            return None
        return json.loads(_fernet.decrypt(value).decode("utf-8"))
