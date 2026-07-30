from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.db import get_db
from identity_api.deps import (
    AuthContext,
    clear_session_cookie,
    client_ip,
    get_current_auth,
    get_current_user,
    set_session_cookie,
)
from identity_api.models import User
from identity_api.redis_client import get_redis
from identity_api.schemas import (
    LoginRequest,
    MessageOut,
    RegisterRequest,
    UserOut,
)
from identity_api.security import hash_password, verify_password
from identity_api.services import sessions as session_service
from identity_api.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    email = body.email.lower().strip()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(email=email, password_hash=hash_password(body.password))
    db.add(user)
    await db.flush()

    ip = client_ip(request)
    await write_audit(
        db,
        action="user.register",
        actor_user_id=user.id,
        target_type="user",
        target_id=str(user.id),
        ip_address=ip,
    )

    session, token = await session_service.create_session(
        db,
        redis,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip,
    )
    await write_audit(
        db,
        action="session.create",
        actor_user_id=user.id,
        target_type="session",
        target_id=str(session.id),
        ip_address=ip,
    )
    await db.commit()
    await db.refresh(user)
    set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserOut)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    email = body.email.lower().strip()
    ip = client_ip(request)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if (
        user is None
        or user.password_hash is None
        or not verify_password(user.password_hash, body.password)
    ):
        await write_audit(
            db,
            action="auth.login_failed",
            target_type="user",
            target_id=email,
            ip_address=ip,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        await write_audit(
            db,
            action="auth.login_disabled",
            actor_user_id=user.id,
            target_type="user",
            target_id=str(user.id),
            ip_address=ip,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    session, token = await session_service.create_session(
        db,
        redis,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip,
    )
    await write_audit(
        db,
        action="auth.login",
        actor_user_id=user.id,
        target_type="session",
        target_id=str(session.id),
        ip_address=ip,
    )
    await db.commit()
    await db.refresh(user)
    set_session_cookie(response, token)
    return user


@router.post("/logout", response_model=MessageOut)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    auth: AuthContext = Depends(get_current_auth),
) -> MessageOut:
    await session_service.revoke_session(db, redis, auth.session)
    await write_audit(
        db,
        action="auth.logout",
        actor_user_id=auth.user.id,
        target_type="session",
        target_id=str(auth.session.id),
        ip_address=client_ip(request),
    )
    await db.commit()
    clear_session_cookie(response)
    return MessageOut(message="Logged out")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
