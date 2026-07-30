from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from identity_api.config import settings
from identity_api.redis_client import close_redis
from identity_api.routers import auth, health, me, oauth, passkeys, webauthn


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup hooks go before yield; shutdown after.
    # Close the shared Redis client so connections do not leak on reload/exit.
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Identity Platform API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    # Credentials (cookies) require an explicit origin allowlist — not "*".
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(me.router)
    app.include_router(passkeys.router)
    app.include_router(webauthn.router)
    app.include_router(oauth.router)
    return app


app = create_app()
