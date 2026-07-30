import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from identity_api.config import settings
from identity_api.models import User, WebAuthnCredential

# Short-lived WebAuthn ceremony challenges live in Redis (not Postgres).
_CHALLENGE_TTL_SECONDS = 300


def _register_challenge_key(user_id: UUID) -> str:
    return f"webauthn:register:{user_id}"


def _login_challenge_key(email: str) -> str:
    return f"webauthn:login:{email.lower()}"


async def _store_challenge(redis: Redis, key: str, challenge: bytes) -> None:
    await redis.set(key, bytes_to_base64url(challenge), ex=_CHALLENGE_TTL_SECONDS)


async def _pop_challenge(redis: Redis, key: str) -> bytes | None:
    raw = await redis.get(key)
    if raw is None:
        return None
    await redis.delete(key)
    return base64url_to_bytes(raw)


def _options_dict(options: object) -> dict[str, Any]:
    return json.loads(options_to_json(options))


def _transports_from_strings(
    values: list[str] | None,
) -> list[AuthenticatorTransport] | None:
    if not values:
        return None
    out: list[AuthenticatorTransport] = []
    for value in values:
        try:
            out.append(AuthenticatorTransport(value))
        except ValueError:
            continue
    return out or None


async def list_credentials(
    db: AsyncSession,
    user_id: UUID,
) -> list[WebAuthnCredential]:
    result = await db.execute(
        select(WebAuthnCredential)
        .where(WebAuthnCredential.user_id == user_id)
        .order_by(WebAuthnCredential.created_at.desc())
    )
    return list(result.scalars().all())


async def get_credential_by_id(
    db: AsyncSession,
    credential_id: str,
) -> WebAuthnCredential | None:
    result = await db.execute(
        select(WebAuthnCredential).where(
            WebAuthnCredential.credential_id == credential_id
        )
    )
    return result.scalar_one_or_none()


async def begin_registration(
    db: AsyncSession,
    redis: Redis,
    user: User,
) -> dict[str, Any]:
    existing = await list_credentials(db, user.id)
    exclude = [
        PublicKeyCredentialDescriptor(
            id=base64url_to_bytes(cred.credential_id),
            transports=_transports_from_strings(cred.transports),
        )
        for cred in existing
    ]
    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user.id.bytes,
        user_name=user.email,
        user_display_name=user.email,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    await _store_challenge(redis, _register_challenge_key(user.id), options.challenge)
    return _options_dict(options)


async def complete_registration(
    db: AsyncSession,
    redis: Redis,
    user: User,
    credential: dict[str, Any],
    device_name: str | None,
) -> WebAuthnCredential:
    challenge = await _pop_challenge(redis, _register_challenge_key(user.id))
    if challenge is None:
        raise ValueError("Registration challenge expired or missing")

    verification = verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin_list,
    )

    credential_id = bytes_to_base64url(verification.credential_id)
    existing = await get_credential_by_id(db, credential_id)
    if existing is not None:
        raise ValueError("Credential already registered")

    transports = credential.get("response", {}).get("transports")
    row = WebAuthnCredential(
        user_id=user.id,
        credential_id=credential_id,
        public_key=bytes_to_base64url(verification.credential_public_key),
        sign_count=verification.sign_count,
        transports=list(transports) if transports else None,
        device_name=device_name or "Passkey",
    )
    db.add(row)
    await db.flush()
    return row


async def begin_login(
    db: AsyncSession,
    redis: Redis,
    email: str,
) -> dict[str, Any]:
    normalized = email.lower().strip()
    result = await db.execute(select(User).where(User.email == normalized))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise ValueError("No passkeys available for this account")

    credentials = await list_credentials(db, user.id)
    if not credentials:
        raise ValueError("No passkeys available for this account")

    allow = [
        PublicKeyCredentialDescriptor(
            id=base64url_to_bytes(cred.credential_id),
            transports=_transports_from_strings(cred.transports),
        )
        for cred in credentials
    ]
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=allow,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    await _store_challenge(redis, _login_challenge_key(normalized), options.challenge)
    return _options_dict(options)


async def complete_login(
    db: AsyncSession,
    redis: Redis,
    email: str,
    credential: dict[str, Any],
) -> User:
    normalized = email.lower().strip()
    challenge = await _pop_challenge(redis, _login_challenge_key(normalized))
    if challenge is None:
        raise ValueError("Login challenge expired or missing")

    result = await db.execute(select(User).where(User.email == normalized))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise ValueError("Invalid passkey login")

    credential_id = credential.get("id")
    if not isinstance(credential_id, str):
        raise ValueError("Invalid credential")

    stored = await get_credential_by_id(db, credential_id)
    if stored is None or stored.user_id != user.id:
        raise ValueError("Unknown credential")

    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=settings.webauthn_rp_id,
        expected_origin=settings.webauthn_origin_list,
        credential_public_key=base64url_to_bytes(stored.public_key),
        credential_current_sign_count=stored.sign_count,
    )
    stored.sign_count = verification.new_sign_count
    stored.last_used_at = datetime.now(UTC)
    await db.flush()
    return user
