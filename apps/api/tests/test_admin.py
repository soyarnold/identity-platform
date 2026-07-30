from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.models import User


async def _promote_admin(db: AsyncSession, email: str) -> None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one()
    user.is_admin = True
    await db.commit()


async def test_admin_requires_auth(client: AsyncClient) -> None:
    res = await client.get("/admin/users")
    assert res.status_code == 401


async def test_admin_requires_admin_role(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = await client.get("/admin/users")
    assert res.status_code == 403
    assert res.json()["detail"] == "Admin access required"


async def test_admin_users_disable_and_audit(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "password123"},
    )
    await _promote_admin(db_session, "admin@example.com")
    # Re-login so /auth/me-style session still works; role is read from DB per request.
    await client.post("/auth/logout")
    await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )

    other = await client.post(
        "/auth/register",
        json={"email": "member@example.com", "password": "password123"},
    )
    # Register sets a new sid for member — switch back to admin.
    await client.post("/auth/logout")
    await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )

    member_id = other.json()["id"]
    users = await client.get("/admin/users")
    assert users.status_code == 200
    body = users.json()
    assert body["total"] >= 2
    assert any(u["email"] == "member@example.com" for u in body["items"])

    disabled = await client.patch(
        f"/admin/users/{member_id}",
        json={"is_active": False},
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False

    # Disabled user cannot log in.
    await client.post("/auth/logout")
    login = await client.post(
        "/auth/login",
        json={"email": "member@example.com", "password": "password123"},
    )
    assert login.status_code == 403

    await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "password123"},
    )
    logs = await client.get("/admin/audit-logs", params={"action": "admin.user.update"})
    assert logs.status_code == 200
    assert logs.json()["total"] >= 1
    assert logs.json()["items"][0]["action"] == "admin.user.update"


async def test_admin_oauth_client_crud(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(
        "/auth/register",
        json={"email": "admin2@example.com", "password": "password123"},
    )
    await _promote_admin(db_session, "admin2@example.com")
    await client.post("/auth/logout")
    await client.post(
        "/auth/login",
        json={"email": "admin2@example.com", "password": "password123"},
    )

    created = await client.post(
        "/admin/oauth/clients",
        json={
            "name": "Admin Demo",
            "client_id": "admin-demo",
            "redirect_uris": ["http://localhost:5174/callback"],
            "is_confidential": False,
        },
    )
    assert created.status_code == 201
    assert created.json()["client_id"] == "admin-demo"

    listed = await client.get("/admin/oauth/clients")
    assert listed.status_code == 200
    assert any(c["client_id"] == "admin-demo" for c in listed.json()["items"])

    updated = await client.patch(
        "/admin/oauth/clients/admin-demo",
        json={"name": "Admin Demo Renamed"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Admin Demo Renamed"

    deleted = await client.delete("/admin/oauth/clients/admin-demo")
    assert deleted.status_code == 200

    listed2 = await client.get("/admin/oauth/clients")
    assert all(c["client_id"] != "admin-demo" for c in listed2.json()["items"])


async def test_admin_cannot_disable_self(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await client.post(
        "/auth/register",
        json={"email": "solo-admin@example.com", "password": "password123"},
    )
    await _promote_admin(db_session, "solo-admin@example.com")
    await client.post("/auth/logout")
    me = await client.post(
        "/auth/login",
        json={"email": "solo-admin@example.com", "password": "password123"},
    )
    uid = me.json()["id"]
    res = await client.patch(f"/admin/users/{uid}", json={"is_active": False})
    assert res.status_code == 400
