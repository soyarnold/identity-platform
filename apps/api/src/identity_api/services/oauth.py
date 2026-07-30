import base64
import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.config import settings
from identity_api.models import (
    OAuthAccessToken,
    OAuthClient,
    OAuthRefreshToken,
    User,
)
from identity_api.security import generate_session_token, hash_token

_AUTH_CODE_TTL_SECONDS = 300
_DEFAULT_SCOPES = "openid profile email"


def _code_redis_key(code: str) -> str:
    return f"oauth:code:{code}"


def verify_pkce_s256(code_verifier: str, code_challenge: str) -> bool:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return secrets.compare_digest(computed, code_challenge)


async def get_client(db: AsyncSession, client_id: str) -> OAuthClient | None:
    result = await db.execute(
        select(OAuthClient).where(OAuthClient.client_id == client_id)
    )
    return result.scalar_one_or_none()


def validate_redirect_uri(client: OAuthClient, redirect_uri: str) -> bool:
    return redirect_uri in (client.redirect_uris or [])


async def issue_authorization_code(
    redis: Redis,
    *,
    client_id: str,
    user_id: UUID,
    redirect_uri: str,
    code_challenge: str,
    code_challenge_method: str,
    scopes: str,
) -> str:
    # One-time code in Redis — short TTL, never durable in Postgres.
    code = secrets.token_urlsafe(32)
    payload = {
        "client_id": client_id,
        "user_id": str(user_id),
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "scopes": scopes,
    }
    await redis.set(
        _code_redis_key(code),
        json.dumps(payload),
        ex=_AUTH_CODE_TTL_SECONDS,
    )
    return code


async def consume_authorization_code(
    redis: Redis,
    code: str,
) -> dict[str, Any] | None:
    raw = await redis.get(_code_redis_key(code))
    if raw is None:
        return None
    await redis.delete(_code_redis_key(code))
    return json.loads(raw)


def build_redirect_url(redirect_uri: str, **params: str) -> str:
    sep = "&" if "?" in redirect_uri else "?"
    return f"{redirect_uri}{sep}{urlencode(params)}"


async def issue_tokens(
    db: AsyncSession,
    *,
    client_id: str,
    user_id: UUID,
    scopes: str,
) -> dict[str, Any]:
    access = generate_session_token()
    refresh = generate_session_token()
    now = datetime.now(UTC)
    access_expires = now + timedelta(seconds=settings.access_token_ttl_seconds)
    refresh_expires = now + timedelta(seconds=settings.refresh_token_ttl_seconds)

    db.add(
        OAuthAccessToken(
            token_hash=hash_token(access),
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=access_expires,
        )
    )
    db.add(
        OAuthRefreshToken(
            token_hash=hash_token(refresh),
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=refresh_expires,
        )
    )
    await db.flush()
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": settings.access_token_ttl_seconds,
        "refresh_token": refresh,
        "scope": scopes,
    }


async def get_access_token_row(
    db: AsyncSession,
    token: str,
) -> OAuthAccessToken | None:
    result = await db.execute(
        select(OAuthAccessToken).where(
            OAuthAccessToken.token_hash == hash_token(token),
            OAuthAccessToken.revoked_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        return None
    return row


async def rotate_refresh_token(
    db: AsyncSession,
    *,
    refresh_token: str,
    client_id: str,
) -> dict[str, Any] | None:
    result = await db.execute(
        select(OAuthRefreshToken).where(
            OAuthRefreshToken.token_hash == hash_token(refresh_token),
            OAuthRefreshToken.revoked_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if row is None or row.client_id != client_id:
        return None
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        return None

    row.revoked_at = datetime.now(UTC)
    return await issue_tokens(
        db,
        client_id=row.client_id,
        user_id=row.user_id,
        scopes=row.scopes,
    )


async def get_user_for_access_token(
    db: AsyncSession,
    token: str,
) -> tuple[User, OAuthAccessToken] | None:
    row = await get_access_token_row(db, token)
    if row is None:
        return None
    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    return user, row


def normalize_scopes(scope: str | None) -> str:
    if not scope or not scope.strip():
        return _DEFAULT_SCOPES
    return " ".join(scope.split())
