import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.token import TokenPair
from app.services.user_service import create_user, get_user_by_email, get_user_by_username, increment_token_version


async def register(db: AsyncSession, email: str, username: str, password: str) -> tuple[User, TokenPair]:
    if await get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    if await get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    hashed = hash_password(password)
    user = await create_user(db, email, username, hashed)
    token_pair = await _create_token_pair(db, user)
    return user, token_pair


async def login(db: AsyncSession, email: str, password: str) -> tuple[User, TokenPair]:
    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    token_pair = await _create_token_pair(db, user)
    return user, token_pair


async def refresh(db: AsyncSession, raw_refresh_token: str) -> TokenPair:
    token_hash = hash_token(raw_refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    if stored_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    stored_token.is_revoked = True

    user_result = await db.execute(select(User).where(User.id == stored_token.user_id))
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    token_pair = await _create_token_pair(db, user)
    return token_pair


async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
    token_hash = hash_token(raw_refresh_token)
    await db.execute(
        update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(is_revoked=True)
    )
    await db.commit()


async def logout_all_devices(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(RefreshToken).where(RefreshToken.user_id == user_id).values(is_revoked=True)
    )
    await increment_token_version(db, user_id)


async def _create_token_pair(db: AsyncSession, user: User) -> TokenPair:
    access = create_access_token(
        user_id=user.id,
        role=user.role,
        token_version=user.token_version,
    )

    raw_refresh = generate_refresh_token()
    refresh_hash = hash_token(raw_refresh)
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.commit()

    return TokenPair(access_token=access, refresh_token=raw_refresh)
