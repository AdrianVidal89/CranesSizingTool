"""Application configuration, read from environment variables.

No secrets are hardcoded. The defaults below are clearly-labeled insecure
placeholders for local development only; a real deployment must override
every one of them via the environment.
"""

from __future__ import annotations

import base64
import hashlib

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_allowed_origins: str = "http://localhost:5173"

    database_url: str = (
        "postgresql+psycopg://cranes:cranes_dev_password@localhost:5432/cranes_sizing"
    )

    # Secret used to derive the Fernet key for column-level encryption at
    # rest (see infrastructure/db/encrypted_types.py). Must be overridden
    # with a high-entropy secret outside local development.
    field_encryption_secret: str = "INSECURE-DEV-ONLY-CHANGE-ME"

    # Whether auth session/CSRF cookies require HTTPS. False only for local
    # HTTP development; must be True in any real deployment.
    session_cookie_secure: bool = True

    # "strict" by default (CLAUDE.md security checklist / ARCHITECTURE.md
    # section 7). The frontend never needs the cookie sent on a cross-site
    # top-level navigation (there is no email-link or third-party-redirect
    # flow into the app), so Strict is safe and is the more defensive
    # choice. Exposed as a setting only in case a future flow genuinely
    # needs Lax; document the reason here if it's ever changed.
    session_cookie_samesite: str = "strict"

    session_ttl_hours: int = 24 * 7

    # "production" disables the interactive API docs (/docs, /redoc) —
    # their bundled Swagger/Redoc UI loads third-party CDN scripts, which
    # would either violate our CSP or need it relaxed. Reducing attack
    # surface in production is simpler than carving out CSP exceptions.
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return self.cors_allowed_origins.split(",")


settings = Settings()


def derive_fernet_key(secret: str) -> bytes:
    """Derive a valid 32-byte urlsafe-base64 Fernet key from an arbitrary secret."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)
