import pytest
from httpx import ASGITransport, AsyncClient

from identity_api.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
