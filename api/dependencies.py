"""
FastAPI dependency injection.

Provides reusable dependencies for:
- Database session management
- JWT token verification
- Current user extraction
"""

from __future__ import annotations

import os
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database.db_setup import SessionLocal
from database.repositories import UserRepository
from database.models import User


# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session per request.

    Automatically commits on success and rolls back on error.

    Yields:
        SQLAlchemy Session.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_access_token(user_id: int, username: str) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User database ID.
        username: Username for the token.

    Returns:
        Encoded JWT token string.
    """
    from datetime import datetime, timedelta

    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate the current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from request header.
        db: Database session.

    Returns:
        Authenticated User model instance.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 401: If user not found or inactive.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id = int(payload.get("sub", 0))
        if user_id == 0:
            raise JWTError("Invalid token")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current user without raising on missing token.

    Used for endpoints that work both authenticated and anonymous.

    Args:
        credentials: Optional HTTP Bearer credentials.
        db: Database session.

    Returns:
        User if authenticated, None otherwise.
    """
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
