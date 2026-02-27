import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    role: UserRole
    avatar_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicUserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole
    avatar_url: str | None

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    username: str | None = None
    avatar_url: str | None = None


class ChangeRoleRequest(BaseModel):
    role: UserRole
