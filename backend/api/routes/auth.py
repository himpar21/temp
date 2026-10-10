"""Signup, login, session, and logout endpoints."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from core.security import (
    JWT_COOKIE_NAME,
    create_access_token,
    hash_password,
    verify_password,
)
from database.postgres.connection import get_db
from database.postgres.models import User
from schemas.request.auth_schema import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    SignupRequest,
    UserResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


def _role_for_email(email: str) -> str:
    local_part = email.partition("@")[0].lower()
    return {"admin": "Admin", "user1": "Tester", "user2": "Test Lead"}.get(local_part, "Tester")


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        created_at=user.created_at,
    )


def _set_session_cookie(response: Response, token: str, expires_in: int) -> None:
    response.set_cookie(
        key=JWT_COOKIE_NAME,
        value=token,
        max_age=expires_in,
        httponly=True,
        secure=os.getenv("APP_ENV", "development").lower() == "production",
        samesite="lax",
        path="/",
    )


def _auth_response(user: User, response: Response) -> AuthResponse:
    token, expires_in = create_access_token(user.id)
    _set_session_cookie(response, token, expires_in)
    return AuthResponse(
        access_token=token,
        expires_in=expires_in,
        user=_user_response(user),
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == request.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        full_name=request.full_name,
        role=request.role,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists") from None
    db.refresh(user)
    return _auth_response(user, response)


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == request.email))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _auth_response(user, response)


@router.get("/session", response_model=UserResponse)
def session(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response) -> LogoutResponse:
    response.delete_cookie(key=JWT_COOKIE_NAME, path="/", samesite="lax")
    return LogoutResponse(message="Logged out")
