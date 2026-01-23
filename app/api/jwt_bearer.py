"""JWT Bearer authentication module."""

from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.security import HTTPBearer

from app.core.config import auth_settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.db.redis_client import redis_client
from app.schemas.auth import TokenData


class TokenBearer(HTTPBearer, ABC):
    """JWT Bearer authentication class."""

    def __init__(self, auto_error: bool = True) -> None:
        """Initialize JWTBearer instance."""
        super().__init__(auto_error=auto_error, description="JWT Bearer token authentication.")

    async def __call__(self, request: Request) -> TokenData:  # type: ignore[override]
        """Handle the incoming request for JWT authentication."""
        http_auth_credentials = await super().__call__(request)
        assert http_auth_credentials is not None  # for mypy type checking

        token = http_auth_credentials.credentials

        token_data = decode_token(token)
        if token_data is None:
            raise AuthenticationError(message="Invalid or expired token.")

        if await is_token_revoked(token_data.jti):
            raise AuthenticationError(message="Token has been revoked.")

        self.verify_token_data(token_data)

        return token_data

    @abstractmethod
    def verify_token_data(self, token_data: TokenData) -> None:
        """Verify the JWT token data against expected data.

        Args:
            token_data (TokenData): JWT token data.
        """
        pass


class AccessTokenBearer(TokenBearer):
    """Bearer class to verify access tokens."""

    def verify_token_data(self, token_data: TokenData) -> None:
        """Verify that the token is an access token."""
        if token_data.type != "access":
            raise AuthenticationError("Invalid access token.")


class RefreshTokenBearer(TokenBearer):
    """Bearer class to verify refresh tokens."""

    def verify_token_data(self, token_data: TokenData) -> None:
        """Verify that the token is a refresh token."""
        if token_data.type != "refresh":
            raise AuthenticationError(message="Invalid refresh token.")


async def revoke_token(jti: str) -> None:
    """Revoke a JWT token by adding its JTI to a blacklist.

    Args:
        jti (str): The JWT ID to revoke.
    """
    # Store the revoked JTI in Redis with an expiration time
    jti_expiry = auth_settings.jwt_refresh_token_exp_days * 24 * 3600
    await redis_client.set(jti, value="", expire=jti_expiry)


async def is_token_revoked(jti: str) -> bool:
    """Check if a JWT token has been revoked.

    Args:
        jti (str): The JWT ID to check.

    Returns:
        bool: True if the token is revoked, False otherwise.
    """
    return await redis_client.get(jti) is not None
