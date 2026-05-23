import pytest
from fastapi import HTTPException

from app.schemas.token import TokenPair
from app.services import auth_service


@pytest.mark.asyncio
async def test_register_returns_user_and_tokens(monkeypatch, fake_db, sample_user):
    async def fake_get_user_by_email(_db, _email):
        return None

    async def fake_get_user_by_username(_db, _username):
        return None

    async def fake_create_user(_db, _email, _username, _hashed_password):
        return sample_user

    async def fake_create_token_pair(_db, _user):
        return TokenPair(access_token="access-token", refresh_token="refresh-token")

    monkeypatch.setattr(auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_service, "get_user_by_username", fake_get_user_by_username)
    monkeypatch.setattr(auth_service, "create_user", fake_create_user)
    monkeypatch.setattr(auth_service, "_create_token_pair", fake_create_token_pair)
    monkeypatch.setattr(auth_service, "hash_password", lambda _password: "hashed-pass")

    user, token_pair = await auth_service.register(
        fake_db,
        "new@example.com",
        "new_user",
        "new-password",
    )

    assert user.id == sample_user.id
    assert token_pair.access_token == "access-token"


@pytest.mark.asyncio
async def test_login_raises_on_invalid_password(monkeypatch, fake_db, sample_user):
    async def fake_get_user_by_email(_db, _email):
        return sample_user

    monkeypatch.setattr(auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_service, "verify_password", lambda _plain, _hashed: False)

    with pytest.raises(HTTPException) as exc:
        await auth_service.login(fake_db, "smoke@example.com", "bad-password")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid email or password"


@pytest.mark.asyncio
async def test_refresh_raises_on_missing_token(monkeypatch, fake_db):
    class FakeResult:
        def scalar_one_or_none(self):
            return None

    async def fake_execute(_query):
        return FakeResult()

    fake_db.execute = fake_execute
    monkeypatch.setattr(auth_service, "hash_token", lambda _raw: "token-hash")

    with pytest.raises(HTTPException) as exc:
        await auth_service.refresh(fake_db, "refresh-token")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or revoked refresh token"
