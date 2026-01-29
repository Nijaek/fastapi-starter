import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.redis import get_redis

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(subject: int, token_type: str, expires_delta: timedelta) -> tuple[str, str]:
    """Create a JWT token with the given subject and expiration.

    Returns:
        tuple[str, str]: (token, jti) - The encoded JWT token and its unique identifier.
    """
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": token_type,
        "jti": jti,
    }
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def create_access_token(subject: int) -> tuple[str, str]:
    """Create an access token for the given user ID.

    Returns:
        tuple[str, str]: (token, jti)
    """
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: int) -> tuple[str, str]:
    """Create a refresh token for the given user ID.

    Returns:
        tuple[str, str]: (token, jti)
    """
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def store_refresh_token(user_id: int, jti: str, expires_in_seconds: int) -> None:
    """Store refresh token JTI in Redis.

    Stores both the token lookup key and a user->token mapping for bulk revocation.
    """
    redis = await get_redis()
    # Store the refresh token with TTL
    token_key = f"refresh_token:{jti}"
    await redis.setex(token_key, expires_in_seconds, str(user_id))
    # Store user->token mapping for bulk revocation
    user_token_key = f"user_tokens:{user_id}:{jti}"
    await redis.setex(user_token_key, expires_in_seconds, "1")


async def is_token_revoked(jti: str) -> bool:
    """Check if a refresh token has been revoked.

    A token is considered revoked if it doesn't exist in Redis.
    """
    redis = await get_redis()
    key = f"refresh_token:{jti}"
    return not await redis.exists(key)


async def revoke_token(jti: str) -> None:
    """Revoke a single refresh token."""
    redis = await get_redis()
    # Get user_id from token before deleting
    token_key = f"refresh_token:{jti}"
    user_id = await redis.get(token_key)
    await redis.delete(token_key)
    # Also delete user->token mapping if we found the user
    if user_id:
        user_token_key = f"user_tokens:{user_id}:{jti}"
        await redis.delete(user_token_key)


async def revoke_all_user_tokens(user_id: int) -> None:
    """Revoke all refresh tokens for a user (e.g., on password change).

    Uses pattern matching to find and delete all tokens for the user.
    """
    redis = await get_redis()
    pattern = f"user_tokens:{user_id}:*"
    # Collect all JTIs first, then delete
    keys_to_delete = []
    async for key in redis.scan_iter(pattern):
        keys_to_delete.append(key)
        # Extract JTI from key and add refresh_token key
        jti = key.split(":")[-1]
        keys_to_delete.append(f"refresh_token:{jti}")
    # Delete all keys
    if keys_to_delete:
        await redis.delete(*keys_to_delete)
