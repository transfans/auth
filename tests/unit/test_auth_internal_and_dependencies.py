from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core import dependencies
from app.models.enums import UserRole
from app.schemas.token import ValidateTokenResponse


@pytest.mark.asyncio
async def test_validate_token_returns_invalid_when_decode_fails(monkeypatch, auth_client):
    from app.api import internal as internal_api

    monkeypatch.setattr(internal_api, "decode_access_token", lambda _token: None)

    response = await auth_client.post("/auth/validate-token", json={"token": "bad-token"})

    assert response.status_code == 200
    payload = ValidateTokenResponse(**response.json())
    assert payload.is_valid is False
    assert payload.claims is None


@pytest.mark.asyncio
async def test_validate_token_returns_claims_on_valid_payload(monkeypatch, auth_client, sample_user):
    from app.api import internal as internal_api

    monkeypatch.setattr(
        internal_api,
        "decode_access_token",
        lambda _token: {"sub": str(sample_user.id), "role": UserRole.user.value, "ver": sample_user.token_version},
    )

    response = await auth_client.post("/auth/validate-token", json={"token": "good-token"})

    assert response.status_code == 200
    payload = ValidateTokenResponse(**response.json())
    assert payload.is_valid is True
    assert payload.claims is not None
    assert payload.claims.sub == sample_user.id


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_payload(monkeypatch, fake_db):
    monkeypatch.setattr(dependencies, "decode_access_token", lambda _token: {"role": "user"})

    credentials = type("Creds", (), {"credentials": "bad"})()
    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(credentials, fake_db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token payload"


@pytest.mark.asyncio
async def test_get_current_user_rejects_revoked_token(monkeypatch, fake_db, sample_user):
    sample_user.token_version = 5
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _token: {"sub": str(sample_user.id), "ver": 4, "role": UserRole.user.value},
    )
    monkeypatch.setattr(dependencies, "get_user_by_id", AsyncMock(return_value=sample_user))

    credentials = type("Creds", (), {"credentials": "token"})()
    with pytest.raises(HTTPException) as exc:
        await dependencies.get_current_user(credentials, fake_db)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Token has been revoked"


@pytest.mark.asyncio
async def test_require_admin_rejects_non_admin(sample_user):
    sample_user.role = UserRole.user

    with pytest.raises(HTTPException) as exc:
        await dependencies.require_admin(sample_user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Admin privileges required"
