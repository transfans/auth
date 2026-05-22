from unittest.mock import AsyncMock

import pytest

from app.schemas.token import TokenPair


@pytest.mark.asyncio
async def test_register_publishes_user_registered_contract(monkeypatch, auth_client, sample_user):
    from app.api import auth as auth_api

    publish_event = AsyncMock()
    monkeypatch.setattr(
        auth_api.auth_service,
        "register",
        AsyncMock(return_value=(sample_user, TokenPair(access_token="a", refresh_token="r"))),
    )
    monkeypatch.setattr(auth_api, "publish_event", publish_event)

    response = await auth_client.post(
        "/auth/register",
        json={"email": "new@example.com", "username": "new_user", "password": "password123"},
    )

    assert response.status_code == 201
    publish_event.assert_awaited_once()
    event_name, payload = publish_event.await_args.args
    assert event_name == "user.registered"
    assert payload["user_id"] == str(sample_user.id)
    assert payload["email"] == sample_user.email
    assert payload["username"] == sample_user.username
    assert payload["role"] == sample_user.role.value


@pytest.mark.asyncio
async def test_login_publishes_user_login_contract(monkeypatch, auth_client, sample_user):
    from app.api import auth as auth_api

    publish_event = AsyncMock()
    monkeypatch.setattr(
        auth_api.auth_service,
        "login",
        AsyncMock(return_value=(sample_user, TokenPair(access_token="a", refresh_token="r"))),
    )
    monkeypatch.setattr(auth_api, "publish_event", publish_event)

    response = await auth_client.post(
        "/auth/login",
        json={"email": sample_user.email, "password": "password123"},
    )

    assert response.status_code == 200
    publish_event.assert_awaited_once()
    event_name, payload = publish_event.await_args.args
    assert event_name == "user.login"
    assert payload["user_id"] == str(sample_user.id)
    assert payload["email"] == sample_user.email
