"""
Authentication router.

Endpoints:
    POST /auth/register  — create a new user account (HTTP 201)
    POST /auth/login     — validate credentials and issue a token (HTTP 200)
    POST /auth/refresh   — validate current token and issue a new one (HTTP 200)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.exceptions import AuthError, ConflictError

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Create a new user with a bcrypt-hashed password and return an access token.

    Raises:
        ConflictError (HTTP 409): if the e-mail address is already registered.
    """
    # Check for duplicate e-mail
    result = await db.execute(select(User).where(User.email == body.email))
    existing: User | None = result.scalar_one_or_none()
    if existing is not None:
        raise ConflictError("E-mail já cadastrado.")

    # Create user
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.flush()  # populate user.id before using it

    access_token = create_access_token(user_id=str(user.id), email=user.email)
    return TokenResponse(access_token=access_token)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain an access token",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Validate e-mail and password, then return an access token.

    A generic error is raised regardless of whether the e-mail or the
    password is wrong, to avoid user enumeration.

    Raises:
        AuthError (HTTP 401): if credentials are invalid.
    """
    _invalid_msg = "Credenciais inválidas."

    result = await db.execute(select(User).where(User.email == body.email))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise AuthError(_invalid_msg)

    access_token = create_access_token(user_id=str(user.id), email=user.email)
    return TokenResponse(access_token=access_token)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh an access token",
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Validate the current access token and issue a new one with a fresh expiry.

    Raises:
        AuthError (HTTP 401): if the token is invalid or expired.
    """
    payload = decode_token(body.access_token)  # raises AuthError if invalid

    user_id: str = payload["sub"]
    email: str = payload["email"]

    # Verify the user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise AuthError("Usuário não encontrado.")

    new_token = create_access_token(user_id=user_id, email=email)
    return TokenResponse(access_token=new_token)
