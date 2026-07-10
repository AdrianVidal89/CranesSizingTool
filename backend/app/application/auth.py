"""Basic authentication use cases: register, login, logout.

Deliberately minimal per Phase 4 scope — no roles/permissions, no password
reset. Depends only on the repository ports (app/application/ports.py) and
the infrastructure/security helpers for hashing, never on SQLAlchemy or
FastAPI directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.application.dto import UserDTO
from app.application.ports import SessionRepository, UserRepository
from app.infrastructure.security.passwords import hash_password, verify_password
from app.infrastructure.security.sessions import generate_token, hash_token


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedSession:
    user: UserDTO
    session_token: str
    csrf_token: str
    expires_at: datetime


class RegisterUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, email: str, password: str) -> UserDTO:
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)
        return self._users.create(email=email, password_hash=hash_password(password))


class LoginUser:
    def __init__(
        self, users: UserRepository, sessions: SessionRepository, session_ttl_hours: int
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._ttl = timedelta(hours=session_ttl_hours)

    def execute(self, email: str, password: str) -> AuthenticatedSession:
        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = generate_token()
        csrf_token = generate_token()
        expires_at = datetime.now(timezone.utc) + self._ttl
        self._sessions.create(
            user_id=user.id,
            token_hash=hash_token(token),
            csrf_token=csrf_token,
            expires_at=expires_at,
        )
        return AuthenticatedSession(
            user=user, session_token=token, csrf_token=csrf_token, expires_at=expires_at
        )


class LogoutUser:
    def __init__(self, sessions: SessionRepository) -> None:
        self._sessions = sessions

    def execute(self, session_id: UUID) -> None:
        self._sessions.delete(session_id)
