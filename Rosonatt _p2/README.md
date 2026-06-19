# Produtos API

API REST profissional para gerenciamento de catálogo de produtos de um e-commerce, desenvolvida com **FastAPI**, **SQLAlchemy**, **PostgreSQL** e **Pytest**.

Projeto estruturado em camadas (Repository → Service → API), com respostas padronizadas, logging estruturado, tratamento global de exceções e suíte de testes de integração contra PostgreSQL real via Docker.

---

## Visão Geral

A API permite criar, listar, buscar, atualizar e remover produtos, além de oferecer:

- Healthcheck (`GET /health`)
- Estatísticas do catálogo (`GET /produtos/stats`)
- Filtros por nome e status ativo
- Paginação (`page`, `limit`)
- Ordenação (`sort=nome|preco|estoque|id|created_at`)

Todas as respostas seguem um envelope padronizado:

```json
{ "success": true, "data": {} }
```

Erros:

```json
{ "success": false, "message": "Descrição do erro" }
```

---

## Tecnologias

| Tecnologia | Uso |
|---|---|
| FastAPI | Framework HTTP |
| SQLAlchemy 2.x | ORM |
| PostgreSQL 16 | Banco relacional |
| Pydantic v2 | Validação e schemas |
| Pytest + TestClient | Testes de integração |
| Docker Compose | Orquestração de containers |
| Uvicorn | Servidor ASGI |

---

## Estrutura do Projeto

```
produtos-api/
├── main.py                  # Entry point (requisito da avaliação)
├── conftest.py              # Fixtures de teste (requisito da avaliação)
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── README.md
├── .env.example
├── app/
│   ├── application.py       # Factory FastAPI
│   ├── core/
│   │   ├── config.py        # Settings por ambiente (.env)
│   │   ├── database.py      # Engine, Session, Base
│   │   └── logging.py       # Logging estruturado
│   ├── models/
│   │   └── produto.py       # Modelo ORM
│   ├── schemas/
│   │   ├── common.py        # Envelopes Success/Error
│   │   └── produto.py       # DTOs Pydantic
│   ├── repositories/
│   │   └── produto_repository.py
│   ├── services/
│   │   └── produto_service.py
│   ├── dependencies/
│   │   └── database.py      # get_db (DI)
│   ├── exceptions/
│   │   └── handlers.py      # Handlers globais
│   └── api/
│       ├── health.py
│       ├── produtos.py
│       └── router.py
└── tests/
    ├── __init__.py
    └── test_produtos.py
```

---

## Arquitetura Adotada

```
Request → Router (API) → Service (regras) → Repository (dados) → PostgreSQL
                ↓
         Schemas Pydantic (validação/resposta)
                ↓
         Exception Handlers (respostas padronizadas)
```

**Decisões arquiteturais:**

- **Separation of Concerns**: rotas não acessam o ORM diretamente
- **Dependency Injection**: `get_db` substituível nos testes via `dependency_overrides`
- **Config centralizada**: `pydantic-settings` com suporte a `.env`
- **Respostas padronizadas**: envelope `{ success, data/message }` em todos os endpoints
- **Dois bancos PostgreSQL**: desenvolvimento (5432) e testes (5433), conforme avaliação

---

## Fluxo de Execução

1. `docker compose up -d` sobe PostgreSQL dev, PostgreSQL test e a API
2. A API conecta ao banco via `DATABASE_URL`
3. No startup, `init_db()` garante que as tabelas existam
4. Requisições passam pelas camadas API → Service → Repository
5. Erros são capturados pelos handlers globais e retornam JSON padronizado

---

## Como Executar

### Pré-requisitos

- Docker e Docker Compose
- Python 3.11+ (para testes locais)

### 1. Subir a infraestrutura

```bash
docker compose up -d
```

Aguarde os containers ficarem **healthy**:

```bash
docker compose ps
```

### 2. Acessar a API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### 3. Variáveis de ambiente

Copie o exemplo:

```bash
cp .env.example .env
```
## Defina a string de conexão forçando o acesso local (PowerShell)
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5435/produtos_dev"

---

## Como Testar

### Subir apenas o banco de teste

```bash
docker compose up -d db_test

```

### Instalar dependências (ambiente local)

```bash
pip install -r requirements.txt
```

### Executar testes

```bash
pytest -v
```

### Verificar cobertura (mínimo 95%)

```bash
pytest --cov
```

### Comando de verificação final (avaliação)

```bash
docker compose up -d db_test && pytest --cov=main -v
```

---

## Saída Esperada do Pytest

```
tests/test_produtos.py::test_health_check_retorna_status_saudavel PASSED
tests/test_produtos.py::test_listar_produtos_banco_vazio PASSED
tests/test_produtos.py::test_criar_produto_persiste_no_banco PASSED
...
======================== 35 passed in X.XXs ========================
```

Cobertura esperada: **≥ 95%** em `main` e `app`.

---

## Exemplos de Requests

### Criar produto

```bash
curl -X POST http://localhost:8000/produtos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Camiseta Básica", "preco": 49.90, "estoque": 25, "ativo": true}'
```

### Listar com filtros e paginação

```bash
curl "http://localhost:8000/produtos?nome=camiseta&ativo=true&page=1&limit=10&sort=preco&order=asc"
```

### Buscar por ID

```bash
curl http://localhost:8000/produtos/1
```

### Estatísticas

```bash
curl http://localhost:8000/produtos/stats
```

### Remover produto

```bash
curl -X DELETE http://localhost:8000/produtos/1
```

---

## Exemplos de Responses

### Sucesso — criar produto (201)

```json
{
  "success": true,
  "data": {
    "id": 1,
    "nome": "Camiseta Básica",
    "preco": 49.90,
    "estoque": 25,
    "ativo": true,
    "created_at": "2026-06-18T12:00:00Z",
    "updated_at": "2026-06-18T12:00:00Z"
  }
}
```

### Sucesso — listagem paginada (200)

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "limit": 10,
    "pages": 0
  }
}
```

### Erro — produto não encontrado (404)

```json
{
  "success": false,
  "message": "Produto com id 999 não encontrado"
}
```

### Erro — validação (422)

```json
{
  "success": false,
  "message": "body.preco: Input should be greater than 0"
}
```

---

## Fixtures e Isolamento de Testes

### Fixture `client` (conftest.py)

1. **`Base.metadata.create_all`** — cria tabelas no PostgreSQL de teste (porta 5433)
2. **`app.dependency_overrides[get_db]`** — substitui a sessão pelo banco de teste
3. **`yield TestClient(app)`** — executa o teste
4. **`Base.metadata.drop_all`** — remove todas as tabelas no teardown

Isso garante que **cada teste começa com banco limpo**, independente da ordem de execução.

### Fixture `produto_existente`

Depende de `client` e cria um produto padrão via `POST /produtos`, retornando o objeto `data` para testes de GET/DELETE/UPDATE.

### Por que PostgreSQL real?

Testes contra PostgreSQL detectam bugs de constraints, tipos e transações que SQLite em memória não capturaria — padrão adotado em ambientes profissionais.

---

## Cobertura de Testes

A suíte contém **35 testes** cobrindo:

| Categoria | Quantidade |
|---|---|
| CRUD obrigatório | 9 |
| Validação 422 (parametrizado) | 7 |
| Isolamento | 2 |
| Filtros / paginação / ordenação | 8 |
| Estatísticas | 2 |
| Atualização (PUT/PATCH) | 4 |
| Edge cases | 3 |

Meta de cobertura configurada em `pytest.ini`: **`--cov-fail-under=95`**.

---

## Validações Implementadas

| Campo | Regra |
|---|---|
| `nome` | Obrigatório, 3–100 chars, sem espaços vazios |
| `preco` | Obrigatório, maior que zero |
| `estoque` | Opcional (padrão 0), não negativo |
| `ativo` | Opcional (padrão `true`) |

---

## Possíveis Melhorias Futuras

- Autenticação JWT e controle de permissões
- Soft delete com campo `deleted_at`
- Cache Redis para listagens frequentes
- Migrations com Alembic
- CI/CD com GitHub Actions
- Rate limiting e observabilidade (OpenTelemetry)
- Integração com fila de eventos (Kafka/RabbitMQ) para estoque

---

## Licença

Projeto educacional — uso livre para portfólio e avaliação acadêmica.
