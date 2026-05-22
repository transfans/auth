from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_auth_live_register_login_refresh_logout_flow(live_auth_client):
    email = f"e2e_{uuid4().hex[:10]}@example.com"
    username = f"e2e_user_{uuid4().hex[:10]}"
    password = "Password123!"

    register_response = await live_auth_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["access_token"]
    assert register_payload["refresh_token"]

    login_response = await live_auth_client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["access_token"]
    assert login_payload["refresh_token"]

    refresh_response = await live_auth_client.post(
        "/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200

    logout_response = await live_auth_client.post(
        "/auth/logout",
        json={"refresh_token": login_payload["refresh_token"]},
    )
    assert logout_response.status_code == 204
