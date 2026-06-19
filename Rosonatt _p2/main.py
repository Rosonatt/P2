"""
Ponto de entrada da API de Produtos.

Mantido na raiz conforme requisitos da avaliação — delega a lógica
para o pacote `app/` com arquitetura em camadas.
"""

from app.application import create_app
from app.dependencies.database import get_db

# Instância exposta para uvicorn e TestClient
app = create_app()

# Reexportação necessária para dependency_overrides nos testes
__all__ = ["app", "get_db"]
