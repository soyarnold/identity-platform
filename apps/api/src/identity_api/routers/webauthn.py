from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.db import get_db
from identity_api.deps import (
    client_ip,
    get_current_user,
    set_session_cookie,
)
from identity_api.models import User
from identity_api.redis_client import get_redis
from identity_api.schemas import (
    LoginOptionsOut,
    LoginOptionsRequest,
    LoginVerifyRequest,
    PasskeyOut,
    RegisterOptionsOut,
    RegisterVerifyRequest,
    UserOut,
)
from identity_api.services import sessions as session_service
from identity_api.services import webauthn as webauthn_service
from identity_api.services.audit import write_audit

router = APIRouter(prefix="/webauthn", tags=["webauthn"])


def _credential_payload(body_credential: Any) -> dict[str, Any]:
    # Pydantic model → plain dict for py_webauthn.
    return body_credential.model_dump(by_alias=True, exclude_none=True)


@router.post("/register/options", response_model=RegisterOptionsOut)
async def register_options(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
) -> RegisterOptionsOut:
    options = await webauthn_service.begin_registration(db, redis, user)
    return RegisterOptionsOut(options=options)


@router.post("/register/verify", response_model=PasskeyOut, status_code=201)
async def register_verify(
    body: RegisterVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
) -> PasskeyOut:
    try:
        cred = await webauthn_service.complete_registration(
            db,
            redis,
            user,
            credential=_credential_payload(body.credential),
            device_name=body.device_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passkey registration failed",
        ) from exc

    await write_audit(
        db,
        action="passkey.register",
        actor_user_id=user.id,
        target_type="webauthn_credential",
        target_id=str(cred.id),
        ip_address=client_ip(request),
    )
    await db.commit()
    await db.refresh(cred)
    return PasskeyOut.model_validate(cred)


@router.post("/login/options", response_model=LoginOptionsOut)
async def login_options(
    body: LoginOptionsRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> LoginOptionsOut:
    try:
        options = await webauthn_service.begin_login(db, redis, body.email)
    except ValueError as exc:
        # Avoid account enumeration details beyond a generic message.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return LoginOptionsOut(options=options)


@router.post("/login/verify", response_model=UserOut)
async def login_verify(
    body: LoginVerifyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    ip = client_ip(request)
    try:
        user = await webauthn_service.complete_login(
            db,
            redis,
            body.email,
            credential=_credential_payload(body.credential),
        )
    except ValueError as exc:
        await write_audit(
            db,
            action="auth.passkey_login_failed",
            target_type="user",
            target_id=body.email.lower(),
            ip_address=ip,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        await write_audit(
            db,
            action="auth.passkey_login_failed",
            target_type="user",
            target_id=body.email.lower(),
            ip_address=ip,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Passkey login failed",
        ) from exc

    session, token = await session_service.create_session(
        db,
        redis,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=ip,
    )
    await write_audit(
        db,
        action="auth.passkey_login",
        actor_user_id=user.id,
        target_type="session",
        target_id=str(session.id),
        ip_address=ip,
    )
    await db.commit()
    await db.refresh(user)
    set_session_cookie(response, token)
    return user
