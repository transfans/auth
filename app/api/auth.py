from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.events.publisher import publish_event
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest
from app.schemas.token import TokenPair
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user, tokens = await auth_service.register(db, body.email, body.username, body.password)

    await publish_event(
        "user.registered",
        {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
        },
    )

    return tokens


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    user, tokens = await auth_service.login(db, body.email, body.password)

    await publish_event(
        "user.login",
        {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
        },
    )

    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenPair:
    return await auth_service.refresh(db, body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)) -> None:
    await auth_service.logout(db, body.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Logout from all devices by incrementing token_version and revoking all refresh tokens."""
    await auth_service.logout_all_devices(db, current_user.id)
