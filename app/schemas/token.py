import uuid

from pydantic import BaseModel

from app.models.enums import UserRole


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenClaims(BaseModel):
    sub: uuid.UUID
    role: UserRole
    ver: int


class ValidateTokenRequest(BaseModel):
    token: str


class ValidateTokenResponse(BaseModel):
    is_valid: bool
    claims: TokenClaims | None = None
