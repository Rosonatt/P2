"""Configuração do SQLAlchemy e sessão do banco."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import setup_logging

logger = setup_logging()
settings = get_settings()

engine = create_engine(
    settings.active_database_url,
    pool_pre_ping=True,
    echo=settings.debug,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Classe base declarativa para todos os modelos ORM."""


def init_db() -> None:
    """Cria as tabelas no banco — usado no startup da API."""
    from app.models import produto  # noqa: F401 — registra o modelo no metadata

    logger.info("Inicializando conexão com o banco de dados")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas verificadas/criadas com sucesso")


def get_engine_for_url(database_url: str):
    """Factory de engine — útil para testes com banco dedicado."""
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory_for_url(database_url: str) -> sessionmaker[Session]:
    """Factory de sessão — usada pela fixture de testes."""
    test_engine = get_engine_for_url(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency injection da sessão SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
