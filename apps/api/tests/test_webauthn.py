from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from webauthn.helpers import bytes_to_base64url


@pytest.mark.asyncio
async def test_register_options_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/webauthn/register/options")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_options_and_list_passkeys(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "passkey@example.com", "password": "password123"},
    )
    options = await client.post("/api/webauthn/register/options")
    assert options.status_code == 200
    body = options.json()["options"]
    assert "challenge" in body
    assert body["rp"]["id"] == "localhost"

    listed = await client.get("/api/me/passkeys")
    assert listed.status_code == 200
    assert listed.json() == []


@pytest.mark.asyncio
async def test_register_verify_persists_passkey(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "device@example.com", "password": "password123"},
    )
    assert (await client.post("/api/webauthn/register/options")).status_code == 200

    credential_id = bytes_to_base64url(b"cred-id-bytes-001234")
    verification = MagicMock(
        credential_id=b"cred-id-bytes-001234",
        credential_public_key=b"public-key-bytes",
        sign_count=0,
    )

    with patch(
        "identity_api.services.webauthn.verify_registration_response",
        return_value=verification,
    ):
        response = await client.post(
            "/api/webauthn/register/verify",
            json={
                "device_name": "MacBook",
                "credential": {
                    "id": credential_id,
                    "rawId": credential_id,
                    "type": "public-key",
                    "response": {
                        "attestationObject": "o2NmbXRkbm9uZQ",
                        "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIn0",
                        "transports": ["internal"],
                    },
                },
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["device_name"] == "MacBook"
    assert data["sign_count"] == 0

    listed = await client.get("/api/me/passkeys")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    passkey_id = listed.json()[0]["id"]

    renamed = await client.patch(
        f"/api/me/passkeys/{passkey_id}",
        json={"device_name": "Laptop"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["device_name"] == "Laptop"

    deleted = await client.delete(f"/api/me/passkeys/{passkey_id}")
    assert deleted.status_code == 200
    assert (await client.get("/api/me/passkeys")).json() == []


@pytest.mark.asyncio
async def test_login_options_requires_existing_passkey(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "nopass@example.com", "password": "password123"},
    )
    await client.post("/api/auth/logout")
    response = await client.post(
        "/api/webauthn/login/options",
        json={"email": "nopass@example.com"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_passkey_login_creates_session(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "loginpk@example.com", "password": "password123"},
    )
    assert (await client.post("/api/webauthn/register/options")).status_code == 200

    credential_id = bytes_to_base64url(b"login-cred-bytes-999")
    verification_reg = MagicMock(
        credential_id=b"login-cred-bytes-999",
        credential_public_key=b"pk-bytes",
        sign_count=1,
    )
    with patch(
        "identity_api.services.webauthn.verify_registration_response",
        return_value=verification_reg,
    ):
        created = await client.post(
            "/api/webauthn/register/verify",
            json={
                "credential": {
                    "id": credential_id,
                    "rawId": credential_id,
                    "type": "public-key",
                    "response": {
                        "attestationObject": "o2NmbXRkbm9uZQ",
                        "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIn0",
                    },
                },
            },
        )
    assert created.status_code == 201
    await client.post("/api/auth/logout")

    options = await client.post(
        "/api/webauthn/login/options",
        json={"email": "loginpk@example.com"},
    )
    assert options.status_code == 200
    assert "challenge" in options.json()["options"]

    verification_auth = MagicMock(new_sign_count=2)
    with patch(
        "identity_api.services.webauthn.verify_authentication_response",
        return_value=verification_auth,
    ):
        login = await client.post(
            "/api/webauthn/login/verify",
            json={
                "email": "loginpk@example.com",
                "credential": {
                    "id": credential_id,
                    "rawId": credential_id,
                    "type": "public-key",
                    "response": {
                        "authenticatorData": "AAAA",
                        "clientDataJSON": "eyJ0eXBlIjoid2ViYXV0aG4uZ2V0In0",
                        "signature": "AAAA",
                    },
                },
            },
        )

    assert login.status_code == 200
    assert login.json()["email"] == "loginpk@example.com"
    assert "sid" in login.cookies
    me = await client.get("/api/auth/me")
    assert me.status_code == 200


@pytest.mark.asyncio
async def test_delete_unknown_passkey(client: AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "missingpk@example.com", "password": "password123"},
    )
    response = await client.delete(f"/api/me/passkeys/{uuid4()}")
    assert response.status_code == 404
