from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from identity_api.config import settings
from identity_api.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Identity Platform API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    return app


app = create_app()
