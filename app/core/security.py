"""Security utilities for handling passwords and JWT tokens."""

from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import auth_settings
from app.core.logger import logger
from app.db.redis_client import redis_client
from app.schemas.auth import TokenData, TokenType
from app.utils.datetime import utcnow

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
            Defaults to defaults to settings.JWT_ACCESS_TOKEN_EXP_MINUTES.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = utcnow() + (
        expires_delta or timedelta(minutes=auth_settings.jwt_access_token_exp_minutes)
    )
    to_encode.update({"exp": expire, "type": TokenType.ACCESS.value, "jti": str(uuid4())})
    return jwt.encode(
        to_encode, auth_settings.jwt_secret_key, algorithm=auth_settings.jwt_algorithm
    )


def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a new refresh token.

    Args:
        data (dict): payload data to encode.
        expires_delta (timedelta | None, optional): Expiration time as a timedelta.
            Defaults to defaults to settings.JWT_REFRESH_TOKEN_EXP_DAYS.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = utcnow() + (expires_delta or timedelta(days=auth_settings.jwt_refresh_token_exp_days))
    to_encode.update({"exp": expire, "type": TokenType.REFRESH.value, "jti": str(uuid4())})
    return jwt.encode(
        to_encode, auth_settings.jwt_secret_key, algorithm=auth_settings.jwt_algorithm
    )


def decode_token(token: str) -> TokenData | None:
    """Verify and decode a JWT token.

    Args:
        token (str): The JWT string to verify.

    Returns:
        TokenData | None: The decoded token data or None if verification fails.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            auth_settings.jwt_secret_key,
            algorithms=[auth_settings.jwt_algorithm],
            options={"verify_signature": True, "verify_exp": True},
        )
        return TokenData(
            user_id=UUID(payload["sub"]),
            type=payload["type"],
            jti=payload["jti"],
            exp=payload["exp"],
        )
    except jwt.ExpiredSignatureError:
        logger.info("token_expired")
        return None
    except jwt.InvalidTokenError as exc:
        logger.warning("invalid_token_attempt", error=str(exc), exc_info=True)
        return None
    except jwt.PyJWTError as exc:
        logger.warning("jwt_decode_error", error=str(exc), exc_info=True)
        return None


async def revoke_token(jti: str, exp: int) -> None:
    """Revoke a JWT token by adding its JTI to a blacklist.

    Args:
        jti (str): The JWT ID to revoke.
        exp (int): The expiration time of the token as a UNIX timestamp.
    """
    # Store the revoked JTI in Redis with an expiration time
    jti_expiry = max(0, exp - int(utcnow().timestamp()))
    if jti_expiry > 0:
        await redis_client.set(jti, value="", expire=jti_expiry)


async def is_token_revoked(jti: str) -> bool:
    """Check if a JWT token has been revoked.

    Args:
        jti (str): The JWT ID to check.

    Returns:
        bool: True if the token is revoked, False otherwise.
    """
    return await redis_client.get(jti) is not None
