"""Factory da aplicação FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.exceptions.handlers import register_exception_handlers

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hooks — startup e shutdown da API."""
    settings = get_settings()
    logger.info("Inicializando %s v%s [%s]", settings.app_name, settings.app_version, settings.environment)
    init_db()
    logger.info("API pronta para receber requisições")
    yield
    logger.info("Encerrando aplicação")


def create_app() -> FastAPI:
    """Cria e configura a instância FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "API REST para gerenciamento de produtos de um e-commerce. "
            "Desenvolvida com FastAPI, SQLAlchemy e PostgreSQL."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)
    app.include_router(api_router)

    return app
