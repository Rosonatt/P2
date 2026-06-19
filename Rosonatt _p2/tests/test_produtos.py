"""Testes de integração da API de Produtos."""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def criar_produto(client: TestClient, **overrides) -> dict:
    payload = {
        "nome": "Produto Padrão",
        "preco": 49.90,
        "estoque": 10,
        "ativo": True,
        **overrides,
    }
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    return response.json()["data"]


# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------

def test_health_check_retorna_status_saudavel(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] in {"healthy", "degraded"}
    assert body["data"]["database"] == "connected"


# ---------------------------------------------------------------------------
# CRUD — requisitos obrigatórios da avaliação
# ---------------------------------------------------------------------------

def test_listar_produtos_banco_vazio(client: TestClient) -> None:
    response = client.get("/produtos")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


def test_criar_produto_persiste_no_banco(client: TestClient) -> None:
    payload = {"nome": "Notebook Gamer", "preco": 4599.99, "estoque": 3}
    response = client.post("/produtos", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    produto = body["data"]
    assert produto["id"] is not None
    assert produto["nome"] == "Notebook Gamer"
    assert produto["preco"] == 4599.99
    assert produto["estoque"] == 3
    assert produto["ativo"] is True

    get_response = client.get(f"/produtos/{produto['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["nome"] == "Notebook Gamer"


def test_criar_produto_aparece_na_listagem(client: TestClient) -> None:
    criar_produto(client, nome="Fone Bluetooth")
    response = client.get("/produtos")
    assert response.status_code == 200
    nomes = [item["nome"] for item in response.json()["data"]["items"]]
    assert "Fone Bluetooth" in nomes


def test_buscar_produto_por_id_sucesso(client: TestClient, produto_existente: dict) -> None:
    response = client.get(f"/produtos/{produto_existente['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == produto_existente["id"]
    assert body["data"]["nome"] == produto_existente["nome"]


def test_buscar_produto_id_inexistente_retorna_404(client: TestClient) -> None:
    response = client.get("/produtos/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert "não encontrado" in body["message"]


def test_deletar_produto_retorna_204(client: TestClient, produto_existente: dict) -> None:
    response = client.delete(f"/produtos/{produto_existente['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_deletar_produto_remove_do_banco(client: TestClient, produto_existente: dict) -> None:
    produto_id = produto_existente["id"]
    client.delete(f"/produtos/{produto_id}")
    response = client.get(f"/produtos/{produto_id}")
    assert response.status_code == 404


def test_deletar_produto_inexistente_retorna_404(client: TestClient) -> None:
    response = client.delete("/produtos/88888")
    assert response.status_code == 404
    assert response.json()["success"] is False


# ---------------------------------------------------------------------------
# Validação — payloads inválidos (422)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "payload,expected_fragment",
    [
        ({"nome": "AB", "preco": 10.0}, "nome"),
        ({"nome": "   ", "preco": 10.0}, "nome"),
        ({"preco": 10.0}, "nome"),
        ({"nome": "Produto Válido", "preco": 0}, "preco"),
        ({"nome": "Produto Válido", "preco": -5}, "preco"),
        ({"nome": "Produto Válido", "preco": 10.0, "estoque": -1}, "estoque"),
        ({"nome": "X" * 101, "preco": 10.0}, "nome"),
    ],
)
def test_criar_produto_payload_invalido_retorna_422(
    client: TestClient,
    payload: dict,
    expected_fragment: str,
) -> None:
    response = client.post("/produtos", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert expected_fragment in body["message"].lower()


# ---------------------------------------------------------------------------
# Isolamento entre testes
# ---------------------------------------------------------------------------

def test_isolamento_primeiro_teste_cria_produto(client: TestClient) -> None:
    criar_produto(client, nome="Isolamento A")
    response = client.get("/produtos")
    assert response.json()["data"]["total"] == 1


def test_isolamento_segundo_teste_banco_limpo(client: TestClient) -> None:
    response = client.get("/produtos")
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 0


# ---------------------------------------------------------------------------
# Filtros, paginação e ordenação
# ---------------------------------------------------------------------------

@pytest.fixture
def catalogo(client: TestClient) -> list[dict]:
    produtos = [
        {"nome": "Alpha Produto", "preco": 100.0, "estoque": 50, "ativo": True},
        {"nome": "Beta Produto", "preco": 50.0, "estoque": 10, "ativo": False},
        {"nome": "Gamma Item", "preco": 200.0, "estoque": 5, "ativo": True},
    ]
    return [criar_produto(client, **p) for p in produtos]


def test_filtrar_produtos_por_nome(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos", params={"nome": "alpha"})
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["nome"] == "Alpha Produto"


def test_filtrar_produtos_por_ativo(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos", params={"ativo": True})
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert len(items) == 2
    assert all(item["ativo"] for item in items)


def test_paginacao_produtos(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos", params={"page": 1, "limit": 2})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2

    page2 = client.get("/produtos", params={"page": 2, "limit": 2})
    assert len(page2.json()["data"]["items"]) == 1


@pytest.mark.parametrize(
    "sort_field,expected_first_nome",
    [
        ("nome", "Alpha Produto"),
        ("preco", "Beta Produto"),
        ("estoque", "Gamma Item"),
    ],
)
def test_ordenacao_produtos(
    client: TestClient,
    catalogo: list[dict],
    sort_field: str,
    expected_first_nome: str,
) -> None:
    response = client.get("/produtos", params={"sort": sort_field, "order": "asc", "limit": 100})
    assert response.status_code == 200
    first = response.json()["data"]["items"][0]["nome"]
    assert first == expected_first_nome


def test_ordenacao_desc_por_preco(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos", params={"sort": "preco", "order": "desc"})
    items = response.json()["data"]["items"]
    assert items[0]["preco"] == 200.0


# ---------------------------------------------------------------------------
# Estatísticas
# ---------------------------------------------------------------------------

def test_stats_catalogo_vazio(client: TestClient) -> None:
    response = client.get("/produtos/stats")
    assert response.status_code == 200
    stats = response.json()["data"]
    assert stats["total_produtos"] == 0
    assert stats["estoque_total"] == 0
    assert stats["preco_minimo"] is None


def test_stats_catalogo_com_produtos(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos/stats")
    assert response.status_code == 200
    stats = response.json()["data"]
    assert stats["total_produtos"] == 3
    assert stats["produtos_ativos"] == 2
    assert stats["produtos_inativos"] == 1
    assert stats["estoque_total"] == 65
    assert stats["preco_medio"] == pytest.approx(116.67, rel=0.01)


# ---------------------------------------------------------------------------
# Atualização (melhoria extra)
# ---------------------------------------------------------------------------

def test_atualizar_produto_put(client: TestClient, produto_existente: dict) -> None:
    produto_id = produto_existente["id"]
    payload = {"nome": "Camiseta Atualizada", "preco": 89.90, "estoque": 20, "ativo": False}
    response = client.put(f"/produtos/{produto_id}", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nome"] == "Camiseta Atualizada"
    assert data["preco"] == 89.90
    assert data["ativo"] is False


def test_atualizar_produto_patch_parcial(client: TestClient, produto_existente: dict) -> None:
    produto_id = produto_existente["id"]
    response = client.patch(f"/produtos/{produto_id}", json={"preco": 99.90})
    assert response.status_code == 200
    assert response.json()["data"]["preco"] == 99.90
    assert response.json()["data"]["nome"] == produto_existente["nome"]


def test_atualizar_produto_inexistente_retorna_404(client: TestClient) -> None:
    response = client.put("/produtos/77777", json={"nome": "Teste", "preco": 10.0})
    assert response.status_code == 404


def test_atualizar_sem_campos_retorna_422(client: TestClient, produto_existente: dict) -> None:
    response = client.patch(f"/produtos/{produto_existente['id']}", json={})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_nome_com_espacos_e_normalizado(client: TestClient) -> None:
    response = client.post("/produtos", json={"nome": "  Teclado Mecânico  ", "preco": 299.90})
    assert response.status_code == 201
    assert response.json()["data"]["nome"] == "Teclado Mecânico"


def test_filtro_nome_sem_resultados(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos", params={"nome": "Inexistente"})
    assert response.json()["data"]["total"] == 0


def test_pagina_alem_do_total_retorna_lista_vazia(client: TestClient, catalogo: list[dict]) -> None:
    response = client.get("/produtos", params={"page": 99, "limit": 10})
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
