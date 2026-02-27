import uuid

from fastapi import APIRouter

from app.core.security import decode_access_token
from app.schemas.token import TokenClaims, ValidateTokenRequest, ValidateTokenResponse

router = APIRouter(prefix="/auth", tags=["internal"])


@router.post("/validate-token", response_model=ValidateTokenResponse)
async def validate_token(body: ValidateTokenRequest) -> ValidateTokenResponse:
    payload = decode_access_token(body.token)

    if not payload:
        return ValidateTokenResponse(is_valid=False)

    try:
        claims = TokenClaims(
            sub=uuid.UUID(payload["sub"]),
            role=payload["role"],
            ver=payload["ver"],
        )
        return ValidateTokenResponse(is_valid=True, claims=claims)
    except (KeyError, ValueError):
        return ValidateTokenResponse(is_valid=False)
