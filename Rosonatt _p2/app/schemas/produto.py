"""Schemas Pydantic para o domínio Produto."""

import math
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProdutoBase(BaseModel):
    """Campos compartilhados entre criação e atualização."""

    nome: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nome do produto (3 a 100 caracteres)",
        examples=["Camiseta Básica"],
    )
    preco: float = Field(
        ...,
        gt=0,
        description="Preço em reais — deve ser maior que zero",
        examples=[49.90],
    )
    estoque: int = Field(
        default=0,
        ge=0,
        description="Quantidade em estoque — não pode ser negativa",
        examples=[10],
    )
    ativo: bool = Field(
        default=True,
        description="Indica se o produto está disponível para venda",
        examples=[True],
    )

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, value: str) -> str:
        # Mantemos esta validação aqui para evitar registros inconsistentes no banco.
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("O nome não pode ser vazio ou conter apenas espaços")
        if len(cleaned) < 3:
            raise ValueError("O nome deve ter no mínimo 3 caracteres")
        return cleaned


class ProdutoCreate(ProdutoBase):
    """Payload de criação de produto."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Camiseta Básica",
                "preco": 49.90,
                "estoque": 25,
                "ativo": True,
            }
        }
    )


class ProdutoUpdate(BaseModel):
    """Payload parcial para atualização — todos os campos são opcionais."""

    nome: str | None = Field(default=None, min_length=3, max_length=100)
    preco: float | None = Field(default=None, gt=0)
    estoque: int | None = Field(default=None, ge=0)
    ativo: bool | None = None

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("O nome não pode ser vazio ou conter apenas espaços")
        return cleaned

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> Self:
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("Informe ao menos um campo para atualização")
        return self


class ProdutoResponse(BaseModel):
    """Representação de produto retornada pela API."""

    id: int
    nome: str
    preco: float
    estoque: int
    ativo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProdutoListData(BaseModel):
    """Lista paginada de produtos."""

    items: list[ProdutoResponse]
    total: int
    page: int
    limit: int
    pages: int


class ProdutoStatsData(BaseModel):
    """Estatísticas agregadas do catálogo."""

    total_produtos: int
    produtos_ativos: int
    produtos_inativos: int
    estoque_total: int
    preco_medio: float
    preco_minimo: float | None
    preco_maximo: float | None

    @classmethod
    def from_aggregates(
        cls,
        *,
        total_produtos: int,
        produtos_ativos: int,
        produtos_inativos: int,
        estoque_total: int,
        preco_medio: float,
        preco_minimo: float | None,
        preco_maximo: float | None,
    ) -> "ProdutoStatsData":
        return cls(
            total_produtos=total_produtos,
            produtos_ativos=produtos_ativos,
            produtos_inativos=produtos_inativos,
            estoque_total=estoque_total,
            preco_medio=round(preco_medio, 2),
            preco_minimo=round(preco_minimo, 2) if preco_minimo is not None else None,
            preco_maximo=round(preco_maximo, 2) if preco_maximo is not None else None,
        )


SortField = Literal["nome", "preco", "estoque", "id", "created_at"]
SortOrder = Literal["asc", "desc"]


class ProdutoQueryParams(BaseModel):
    """Parâmetros de consulta para listagem de produtos."""

    nome: str | None = None
    ativo: bool | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort: SortField = "id"
    order: SortOrder = "asc"

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit

    @property
    def total_pages(self) -> int:
        return 1

    def calculate_pages(self, total: int) -> int:
        if total == 0:
            return 0
        return math.ceil(total / self.limit)
