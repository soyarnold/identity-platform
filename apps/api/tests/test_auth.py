import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_me(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["is_admin"] is False
    assert "sid" in response.cookies

    me = await client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "bob@example.com", "password": "password123"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    again = await client.post("/auth/register", json=payload)
    assert again.status_code == 409


@pytest.mark.asyncio
async def test_login_logout_and_sessions(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "password123"},
    )
    await client.post("/auth/logout")

    bad = await client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert bad.status_code == 401

    login = await client.post(
        "/auth/login",
        json={"email": "carol@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    assert "sid" in login.cookies

    sessions = await client.get("/me/sessions")
    assert sessions.status_code == 200
    body = sessions.json()
    assert len(body) >= 1
    assert any(s["is_current"] for s in body)

    session_id = next(s["id"] for s in body if s["is_current"])
    revoked = await client.post(f"/me/sessions/{session_id}/revoke")
    assert revoked.status_code == 200

    me = await client.get("/auth/me")
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401
