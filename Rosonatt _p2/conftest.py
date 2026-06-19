"""
Fixtures compartilhadas para testes de integração com PostgreSQL.

Esta fixture garante que cada teste execute em ambiente limpo:
- create_all antes de cada teste
- drop_all após cada teste
- dependency_overrides substituindo get_db pelo banco de teste (porta 5433)
"""

import os

# Define ambiente de teste antes de importar módulos da aplicação
os.environ.setdefault("ENVIRONMENT", "test")

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_engine_for_url

# Garante releitura das settings com ENVIRONMENT=test
get_settings.cache_clear()

from main import app, get_db

settings = get_settings()
test_engine = get_engine_for_url(str(settings.test_database_url))
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Cliente HTTP de teste com banco PostgreSQL isolado.

    Fluxo:
    1. Cria tabelas (create_all)
    2. Substitui get_db via dependency_overrides
    3. Executa o teste
    4. Remove tabelas (drop_all) — garante isolamento entre testes
    """
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def produto_existente(client: TestClient) -> dict:
    """Cria um produto base reutilizado por testes que precisam de dados pré-existentes."""
    payload = {
        "nome": "Camiseta Premium",
        "preco": 79.90,
        "estoque": 15,
        "ativo": True,
    }
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    return response.json()["data"]
