from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_api import db as db_mod
from identity_api.config import get_settings
from identity_api.models import OAuthClient, User
from identity_api.seed import seed


async def test_seed_idempotent(engine, monkeypatch) -> None:
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "seed-admin@example.com")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "SeedPassword123!")
    monkeypatch.setenv("DEMO_CLIENT_ID", "seed-demo")
    monkeypatch.setenv("DEMO_REDIRECT_URI", "http://localhost:5174/callback")
    monkeypatch.setenv("DEMO_CLIENT_NAME", "Seed Demo")
    get_settings.cache_clear()

    session_factory = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    monkeypatch.setattr(db_mod, "SessionLocal", session_factory)
    monkeypatch.setattr(db_mod, "engine", engine)

    await seed()
    await seed()

    settings = get_settings()
    async with session_factory() as db:
        users = (
            (
                await db.execute(
                    select(User).where(User.email == settings.seed_admin_email)
                )
            )
            .scalars()
            .all()
        )
        clients = (
            (
                await db.execute(
                    select(OAuthClient).where(
                        OAuthClient.client_id == settings.demo_client_id
                    )
                )
            )
            .scalars()
            .all()
        )

    assert len(users) == 1
    assert users[0].is_admin is True
    assert users[0].is_active is True
    assert len(clients) == 1
    assert settings.demo_redirect_uri in clients[0].redirect_uris
