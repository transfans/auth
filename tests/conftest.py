import sys
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api.auth import router as auth_router
from app.api.internal import router as internal_router
from app.api.users import router as users_router
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User


class DummyDbSession:
    async def execute(self, *_args, **_kwargs):  # pragma: no cover - helper
        return None

    async def commit(self):  # pragma: no cover - helper
        return None

    async def refresh(self, *_args, **_kwargs):  # pragma: no cover - helper
        return None

    def add(self, *_args, **_kwargs):  # pragma: no cover - helper
        return None


@pytest.fixture
def auth_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(internal_router)
    return app


@pytest.fixture
def fake_db() -> DummyDbSession:
    return DummyDbSession()


@pytest.fixture
async def auth_client(
    auth_app: FastAPI,
    fake_db: DummyDbSession,
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[DummyDbSession, None]:
        yield fake_db

    auth_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    auth_app.dependency_overrides.clear()


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid4(),
        email="smoke@example.com",
        username="smoke_user",
        hashed_password="hashed-password",
        role=UserRole.user,
        is_active=True,
        token_version=0,
        created_at=datetime.now(UTC),
    )
