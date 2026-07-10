"""Auth endpoints and dependencies: register, login, logout, current user.

The session token lives in an HttpOnly, Secure, SameSite=Lax cookie, so it
is inaccessible to JS and not sent on cross-site navigations. The CSRF
token lives in a separate, non-HttpOnly cookie (readable by frontend JS)
and must be echoed back in the X-CSRF-Token header on every mutating
request (double-submit pattern) — see require_csrf, used by every
state-changing endpoint in this app.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.application.auth import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    LoginUser,
    LogoutUser,
    RegisterUser,
)
from app.application.dto import UserDTO
from app.config import settings
from app.infrastructure.db.repositories import (
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.security.sessions import hash_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE_NAME = "session_token"
CSRF_COOKIE_NAME = "csrf_token"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)


class UserResponse(BaseModel):
    id: UUID
    email: str


def _to_user_response(user: UserDTO) -> UserResponse:
    return UserResponse(id=user.id, email=user.email)


def _set_auth_cookies(response: Response, token: str, csrf_token: str, expires_at: datetime) -> None:
    max_age = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=max_age,
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=max_age,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    use_case = RegisterUser(SqlAlchemyUserRepository(db))
    try:
        user = use_case.execute(payload.email, payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc
    db.commit()
    return _to_user_response(user)


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    use_case = LoginUser(
        SqlAlchemyUserRepository(db), SqlAlchemySessionRepository(db), settings.session_ttl_hours
    )
    try:
        auth_session = use_case.execute(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc
    db.commit()

    _set_auth_cookies(
        response, auth_session.session_token, auth_session.csrf_token, auth_session.expires_at
    )
    return _to_user_response(auth_session.user)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserDTO:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_repo = SqlAlchemySessionRepository(db)
    session = session_repo.get_by_token_hash(hash_token(token))
    if session is None or session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = SqlAlchemyUserRepository(db).get_by_id(session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_csrf(request: Request) -> None:
    """Double-submit CSRF check for any mutating (state-changing) endpoint
    that relies on the cookie-based session (CLAUDE.md: CSRF protection on
    stateful operations)."""
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")
    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is not None:
        session_repo = SqlAlchemySessionRepository(db)
        session = session_repo.get_by_token_hash(hash_token(token))
        if session is not None:
            LogoutUser(session_repo).execute(session.id)
            db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
    response.delete_cookie(CSRF_COOKIE_NAME)


@router.get("/me", response_model=UserResponse)
def me(user: UserDTO = Depends(get_current_user)) -> UserResponse:
    return _to_user_response(user)
