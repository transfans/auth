from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI

from app.core.dependencies import get_current_user, require_admin
from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_logout_returns_204(monkeypatch, auth_client):
    from app.api import auth as auth_api

    monkeypatch.setattr(auth_api.auth_service, "logout", AsyncMock())

    response = await auth_client.post("/auth/logout", json={"refresh_token": "refresh-token"})

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_all_returns_204(monkeypatch, auth_client, auth_app: FastAPI, sample_user):
    from app.api import auth as auth_api

    async def override_get_current_user():
        return sample_user

    auth_app.dependency_overrides[get_current_user] = override_get_current_user
    monkeypatch.setattr(auth_api.auth_service, "logout_all_devices", AsyncMock())

    response = await auth_client.post("/auth/logout-all")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_user_by_id_returns_404_when_missing(monkeypatch, auth_client):
    from app.api import users as users_api

    monkeypatch.setattr(users_api, "get_user_by_id", AsyncMock(return_value=None))

    response = await auth_client.get(f"/users/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_change_role_returns_404_when_target_missing(monkeypatch, auth_client, auth_app: FastAPI, sample_user):
    from app.api import users as users_api

    async def override_require_admin():
        return sample_user

    auth_app.dependency_overrides[require_admin] = override_require_admin
    monkeypatch.setattr(users_api, "get_user_by_id", AsyncMock(return_value=None))

    response = await auth_client.patch(f"/users/{uuid4()}/role", json={"role": UserRole.creator.value})

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_me_returns_409_when_username_taken(monkeypatch, auth_client, auth_app: FastAPI, sample_user):
    from app.api import users as users_api

    async def override_get_current_user():
        return sample_user

    auth_app.dependency_overrides[get_current_user] = override_get_current_user
    taken_user = type("TakenUser", (), {"id": uuid4()})()
    monkeypatch.setattr(users_api, "get_user_by_username", AsyncMock(return_value=taken_user))

    response = await auth_client.put("/users/me", json={"username": "already_used"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken"
