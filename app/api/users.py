import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.events.publisher import publish_event
from app.models.user import User
from app.schemas.user import ChangeRoleRequest, PublicUserResponse, UpdateUserRequest, UserResponse
from app.services.user_service import change_user_role, get_user_by_id, get_user_by_username, update_user_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if body.username is not None:
        existing = await get_user_by_username(db, body.username)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

    return await update_user_profile(db, current_user, body.username, body.avatar_url)


@router.get("/{user_id}", response_model=PublicUserResponse)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_role(
    user_id: uuid.UUID,
    body: ChangeRoleRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    target_user = await get_user_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_role = target_user.role
    updated = await change_user_role(db, user_id, body.role)

    await publish_event(
        "user.role_changed",
        {
            "user_id": str(user_id),
            "old_role": old_role.value,
            "new_role": body.role.value,
        },
    )

    return updated
