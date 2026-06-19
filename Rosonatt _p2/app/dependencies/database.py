"""Dependências de injeção para rotas FastAPI."""

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db as _get_db
from app.services.produto_service import ProdutoService


def get_db() -> Generator[Session, None, None]:
    """Reexporta get_db — ponto central para dependency_overrides nos testes."""
    yield from _get_db()


def get_produto_service(db: Session = Depends(get_db)) -> ProdutoService:
    """Factory do serviço de produtos."""
    return ProdutoService(db)
