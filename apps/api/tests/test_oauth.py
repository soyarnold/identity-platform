import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


@pytest.mark.asyncio
async def test_oauth_pkce_happy_path(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "oauth@example.com", "password": "password123"},
    )
    created = await client.post(
        "/oauth/dev/clients",
        json={
            "name": "Demo",
            "client_id": "demo-app",
            "redirect_uris": ["http://localhost:5174/callback"],
            "is_confidential": False,
        },
    )
    assert created.status_code == 201

    verifier, challenge = _pkce_pair()
    state = "xyz123"

    # Unauthenticated authorize → hosted login redirect
    anon = await client.get(
        "/oauth/authorize",
        params={
            "client_id": "demo-app",
            "redirect_uri": "http://localhost:5174/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "openid profile email",
        },
        follow_redirects=False,
    )
    # client still has sid from register — logout first for this assert
    await client.post("/auth/logout")
    anon = await client.get(
        "/oauth/authorize",
        params={
            "client_id": "demo-app",
            "redirect_uri": "http://localhost:5174/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        },
        follow_redirects=False,
    )
    assert anon.status_code == 302
    assert "/oauth/login" in anon.headers["location"]

    await client.post(
        "/auth/login",
        json={"email": "oauth@example.com", "password": "password123"},
    )
    authed = await client.get(
        "/oauth/authorize",
        params={
            "client_id": "demo-app",
            "redirect_uri": "http://localhost:5174/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        },
        follow_redirects=False,
    )
    assert authed.status_code == 302
    assert "/oauth/consent" in authed.headers["location"]

    consent = await client.post(
        "/oauth/consent",
        json={
            "client_id": "demo-app",
            "redirect_uri": "http://localhost:5174/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "openid profile email",
            "approve": True,
        },
    )
    assert consent.status_code == 200
    redirect_to = consent.json()["redirect_to"]
    assert redirect_to.startswith("http://localhost:5174/callback?")
    qs = parse_qs(urlparse(redirect_to).query)
    assert qs["state"] == [state]
    code = qs["code"][0]

    token = await client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:5174/callback",
            "client_id": "demo-app",
            "code_verifier": verifier,
        },
    )
    assert token.status_code == 200
    body = token.json()
    assert body["token_type"] == "Bearer"
    assert "access_token" in body
    assert "refresh_token" in body

    info = await client.get(
        "/oauth/userinfo",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert info.status_code == 200
    assert info.json()["email"] == "oauth@example.com"

    refreshed = await client.post(
        "/oauth/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": body["refresh_token"],
            "client_id": "demo-app",
        },
    )
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()


@pytest.mark.asyncio
async def test_oauth_rejects_bad_pkce(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "pkce@example.com", "password": "password123"},
    )
    await client.post(
        "/oauth/dev/clients",
        json={
            "name": "Demo2",
            "client_id": "demo-2",
            "redirect_uris": ["http://localhost:5174/callback"],
        },
    )
    _verifier, challenge = _pkce_pair()
    consent = await client.post(
        "/oauth/consent",
        json={
            "client_id": "demo-2",
            "redirect_uri": "http://localhost:5174/callback",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "approve": True,
        },
    )
    code = parse_qs(urlparse(consent.json()["redirect_to"]).query)["code"][0]
    bad = await client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "http://localhost:5174/callback",
            "client_id": "demo-2",
            "code_verifier": "totally-wrong-verifier-value-xxxxxxxx",
        },
    )
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_discovery(client: AsyncClient) -> None:
    response = await client.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    assert response.json()["authorization_endpoint"].endswith("/oauth/authorize")


@pytest.mark.asyncio
async def test_dev_clients_disabled(client: AsyncClient, monkeypatch) -> None:
    from identity_api.config import get_settings

    monkeypatch.setenv("ENABLE_DEV_OAUTH_CLIENTS", "false")
    get_settings.cache_clear()
    try:
        res = await client.post(
            "/oauth/dev/clients",
            json={
                "name": "Nope",
                "client_id": "should-404",
                "redirect_uris": ["http://localhost:5174/callback"],
                "is_confidential": False,
            },
        )
        assert res.status_code == 404
    finally:
        monkeypatch.delenv("ENABLE_DEV_OAUTH_CLIENTS", raising=False)
        get_settings.cache_clear()
