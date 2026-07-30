from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from identity_api.db import get_db
from identity_api.deps import AuthContext, client_ip, get_current_auth
from identity_api.schemas import MessageOut, PasskeyOut, PasskeyRenameRequest
from identity_api.services import webauthn as webauthn_service
from identity_api.services.audit import write_audit

router = APIRouter(prefix="/me/passkeys", tags=["passkeys"])


@router.get("", response_model=list[PasskeyOut])
async def list_passkeys(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
) -> list[PasskeyOut]:
    rows = await webauthn_service.list_credentials(db, auth.user.id)
    return [PasskeyOut.model_validate(row) for row in rows]


@router.patch("/{passkey_id}", response_model=PasskeyOut)
async def rename_passkey(
    passkey_id: UUID,
    body: PasskeyRenameRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
) -> PasskeyOut:
    rows = await webauthn_service.list_credentials(db, auth.user.id)
    target = next((row for row in rows if row.id == passkey_id), None)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passkey not found",
        )
    target.device_name = body.device_name
    await write_audit(
        db,
        action="passkey.rename",
        actor_user_id=auth.user.id,
        target_type="webauthn_credential",
        target_id=str(target.id),
        ip_address=client_ip(request),
    )
    await db.commit()
    await db.refresh(target)
    return PasskeyOut.model_validate(target)


@router.delete("/{passkey_id}", response_model=MessageOut)
async def delete_passkey(
    passkey_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_current_auth),
) -> MessageOut:
    rows = await webauthn_service.list_credentials(db, auth.user.id)
    target = next((row for row in rows if row.id == passkey_id), None)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passkey not found",
        )
    await db.delete(target)
    await write_audit(
        db,
        action="passkey.delete",
        actor_user_id=auth.user.id,
        target_type="webauthn_credential",
        target_id=str(passkey_id),
        ip_address=client_ip(request),
    )
    await db.commit()
    return MessageOut(message="Passkey deleted")
