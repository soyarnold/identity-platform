from datetime import UTC, datetime, timedelta
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.config import settings
from identity_api.models import User, UserSession
from identity_api.security import generate_session_token, hash_token


def _session_redis_key(session_id: UUID) -> str:
    return f"session:{session_id}"


async def create_session(
    db: AsyncSession,
    redis: Redis,
    *,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[UserSession, str]:
    # Return the raw token once for the Set-Cookie response; persist only the hash.
    token = generate_session_token()
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=settings.session_ttl_seconds)
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    db.add(session)
    await db.flush()

    # Redis mirrors active sessions for fast invalidation / future hot-path checks.
    await redis.set(
        _session_redis_key(session.id),
        str(user.id),
        ex=settings.session_ttl_seconds,
    )
    return session, token


async def get_user_for_token(
    db: AsyncSession,
    redis: Redis,
    token: str,
) -> tuple[User, UserSession] | None:
    token_digest = hash_token(token)
    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == token_digest,
            UserSession.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None

    now = datetime.now(UTC)
    expires = session.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires <= now:
        return None

    # Rehydrate Redis if the key expired early but the DB row is still valid.
    cached = await redis.get(_session_redis_key(session.id))
    if cached is None:
        await redis.set(
            _session_redis_key(session.id),
            str(session.user_id),
            ex=max(int((expires - now).total_seconds()), 1),
        )

    user = await db.get(User, session.user_id)
    if user is None or not user.is_active:
        return None
    return user, session


async def revoke_session(
    db: AsyncSession,
    redis: Redis,
    session: UserSession,
) -> None:
    # Soft-revoke in Postgres and drop the Redis key immediately.
    session.revoked_at = datetime.now(UTC)
    await redis.delete(_session_redis_key(session.id))
    await db.flush()


async def list_user_sessions(
    db: AsyncSession,
    user_id: UUID,
) -> list[UserSession]:
    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        .order_by(UserSession.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_all_user_sessions(
    db: AsyncSession,
    redis: Redis,
    user_id: UUID,
) -> int:
    # Used when an admin disables a user so existing sid cookies stop working.
    sessions = await list_user_sessions(db, user_id)
    for session in sessions:
        await revoke_session(db, redis, session)
    return len(sessions)
