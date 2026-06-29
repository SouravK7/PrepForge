"""
Authentication routes.

Handles user registration, login, and profile management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies import create_access_token, get_current_user, get_db
from database.models import User
from database.repositories import UserRepository

router = APIRouter()


# ─── Request / Response Models ────────────────────────────────

class RegisterRequest(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    full_name: str = Field(default="")
    target_role: str = Field(default="Software Engineer")
    experience_level: str = Field(default="Fresher (0-1 years)")


class LoginRequest(BaseModel):
    """User login request."""

    username: str = Field(...)
    password: str = Field(...)


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    target_role: str


class UserProfileResponse(BaseModel):
    """User profile response."""

    user_id: int
    username: str
    email: str
    full_name: str
    target_role: str
    experience_level: str


class UpdateProfileRequest(BaseModel):
    """Profile update request."""

    full_name: str | None = None
    target_role: str | None = None
    experience_level: str | None = None


# ─── Routes ──────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user.

    Creates the account, hashes the password, and returns
    a JWT token so the user is immediately authenticated.

    Args:
        request: Registration details.
        db: Database session.

    Returns:
        TokenResponse with JWT token and user info.

    Raises:
        HTTPException 409: If username or email already exists.
    """
    repo = UserRepository(db)

    try:
        user = repo.create(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            target_role=request.target_role,
            experience_level=request.experience_level,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered.",
        )

    token = create_access_token(user.id, user.username)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        target_role=user.target_role or "",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive access token",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    Args:
        request: Login credentials.
        db: Database session.

    Returns:
        TokenResponse with JWT token.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    repo = UserRepository(db)
    user = repo.authenticate(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(user.id, user.username)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        target_role=user.target_role or "",
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
)
def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Get profile of the authenticated user.

    Args:
        current_user: Authenticated user from JWT.

    Returns:
        UserProfileResponse with profile details.
    """
    return UserProfileResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name or "",
        target_role=current_user.target_role or "",
        experience_level=current_user.experience_level or "",
    )


@router.put(
    "/me",
    response_model=UserProfileResponse,
    summary="Update current user profile",
)
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """
    Update authenticated user's profile.

    Args:
        request: Fields to update.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Updated UserProfileResponse.
    """
    repo = UserRepository(db)
    updated = repo.update_profile(
        user_id=current_user.id,
        full_name=request.full_name,
        target_role=request.target_role,
        experience_level=request.experience_level,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserProfileResponse(
        user_id=updated.id,
        username=updated.username,
        email=updated.email,
        full_name=updated.full_name or "",
        target_role=updated.target_role or "",
        experience_level=updated.experience_level or "",
    )
