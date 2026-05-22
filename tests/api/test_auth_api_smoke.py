from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI

from app.core.dependencies import get_current_user
from app.schemas.token import TokenPair


@pytest.mark.asyncio
async def test_login_success_returns_tokens(monkeypatch, auth_client, sample_user):
    from app.api import auth as auth_api

    monkeypatch.setattr(
        auth_api.auth_service,
        "login",
        AsyncMock(return_value=(sample_user, TokenPair(access_token="access-token", refresh_token="refresh-token"))),
    )
    monkeypatch.setattr(auth_api, "publish_event", AsyncMock())

    response = await auth_client.post(
        "/auth/login",
        json={"email": "smoke@example.com", "password": "valid-password"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "access-token"
    assert payload["refresh_token"] == "refresh-token"


@pytest.mark.asyncio
async def test_login_failure_returns_401(monkeypatch, auth_client):
    from app.api import auth as auth_api
    from fastapi import HTTPException

    monkeypatch.setattr(
        auth_api.auth_service,
        "login",
        AsyncMock(side_effect=HTTPException(status_code=401, detail="Invalid email or password")),
    )
    monkeypatch.setattr(auth_api, "publish_event", AsyncMock())

    response = await auth_client.post(
        "/auth/login",
        json={"email": "smoke@example.com", "password": "invalid-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_refresh_invalid_token_returns_401(monkeypatch, auth_client):
    from app.api import auth as auth_api
    from fastapi import HTTPException

    monkeypatch.setattr(
        auth_api.auth_service,
        "refresh",
        AsyncMock(side_effect=HTTPException(status_code=401, detail="Invalid or revoked refresh token")),
    )

    response = await auth_client.post("/auth/refresh", json={"refresh_token": "bad-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or revoked refresh token"


@pytest.mark.asyncio
async def test_get_me_requires_auth(auth_client):
    response = await auth_client.get("/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_returns_user_when_authenticated(auth_client, auth_app: FastAPI, sample_user):
    async def override_get_current_user():
        return sample_user

    auth_app.dependency_overrides[get_current_user] = override_get_current_user

    response = await auth_client.get("/users/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(sample_user.id)
    assert payload["email"] == sample_user.email
