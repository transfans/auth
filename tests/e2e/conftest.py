import os
from collections.abc import AsyncGenerator

import httpx
import pytest


@pytest.fixture
def live_auth_base_url() -> str:
    return os.getenv("AUTH_E2E_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture
async def live_auth_client(live_auth_base_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    timeout = httpx.Timeout(10.0, connect=2.0)
    async with httpx.AsyncClient(base_url=live_auth_base_url, timeout=timeout) as client:
        try:
            health_response = await client.get("/health")
        except httpx.HTTPError as exc:
            pytest.skip(f"auth e2e skipped: auth service is not reachable ({exc})")

        if health_response.status_code != 200:
            pytest.skip(f"auth e2e skipped: health endpoint returned {health_response.status_code}")

        yield client
