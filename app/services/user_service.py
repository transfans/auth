import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, username: str, hashed_password: str) -> User:
    user = User(email=email, username=username, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_profile(
    db: AsyncSession,
    user: User,
    username: str | None = None,
) -> User:
    if username is not None:
        user.username = username
    await db.commit()
    await db.refresh(user)
    return user


async def change_user_role(db: AsyncSession, user_id: uuid.UUID, new_role: UserRole) -> User | None:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    user.role = new_role
    await db.commit()
    await db.refresh(user)
    print("aaaaaaa" * 100, user.role)
    return user


async def increment_token_version(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(User).where(User.id == user_id).values(token_version=User.token_version + 1)
    )
    await db.commit()
