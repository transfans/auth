import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicUserResponse(BaseModel):
    id: uuid.UUID
    username: str
    role: UserRole

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    username: str | None = None


class ChangeRoleRequest(BaseModel):
    role: UserRole
