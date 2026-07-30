from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.config import settings
from identity_api.db import get_db
from identity_api.models import User, UserSession
from identity_api.redis_client import get_redis
from identity_api.services import sessions as session_service


@dataclass
class AuthContext:
    user: User
    session: UserSession


def client_ip(request: Request) -> str | None:
    # First X-Forwarded-For hop when behind a proxy; else direct peer.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def get_current_auth(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthContext:
    # Session id is the opaque cookie value; only its hash is stored in Postgres.
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    result = await session_service.get_user_for_token(db, redis, token)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    user, session = result
    return AuthContext(user=user, session=session)


async def get_current_user(
    auth: AuthContext = Depends(get_current_auth),
) -> User:
    return auth.user


async def require_admin(
    auth: AuthContext = Depends(get_current_auth),
) -> AuthContext:
    # Admin /admin/* APIs — is_admin set in DB (seed/SQL), not via register.
    if not auth.user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return auth


def set_session_cookie(response: Response, token: str) -> None:
    # HttpOnly keeps the token out of JS; SameSite=Lax covers top-level navigations.
    # cookie_secure/domain stay env-driven for localhost vs CloudFront later.
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        domain=settings.cookie_domain or None,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.cookie_name,
        domain=settings.cookie_domain or None,
        path="/",
    )
