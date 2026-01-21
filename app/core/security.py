"""Security utilities for handling passwords and JWT tokens."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.logger import logger
from app.schemas.user import TokenData

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Generate a hashed password."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a new access token.

    Args:
        data (dict): payload data to encode.
        expires_delta (timedelta | None, optional): Expiration time as a timedelta.
            Defaults to defaults to settings.JWT_DEFAULT_EXP_MINUTES.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_default_exp_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenData | None:
    """Verify and decode a JWT access token..

    Args:
        token (str): The JWT string to verify.

    Returns:
        TokenData | None: The decoded token data or None if verification fails.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_signature": True, "verify_exp": True},
        )
        user_id = payload.get("sub")
        if user_id:
            return TokenData(user_id=UUID(user_id))

        logger.warning("TokenDecodedMissingUserID")
        return None
    except jwt.ExpiredSignatureError:
        logger.info("TokenExpired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("InvalidTokenAttempt", error=str(exc), exc_info=True)
        return None
    except jwt.PyJWTError as exc:
        logger.warning("JWTDecodeError", error=str(exc), exc_info=True)
        return None
