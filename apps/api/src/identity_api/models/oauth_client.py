from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from identity_api.models.base import Base, StringArray


class OAuthClient(Base):
    __tablename__ = "oauth_clients"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    client_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # Null for public PKCE clients; hashed secret for confidential clients.
    client_secret_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    redirect_uris: Mapped[list[str]] = mapped_column(StringArray, default=list)
    is_confidential: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
