"""Repositório de acesso a dados de Produto."""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoQueryParams, ProdutoUpdate, SortField


class ProdutoRepository:
    """Encapsula queries SQLAlchemy — mantém a camada de serviço desacoplada do ORM."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: ProdutoCreate) -> Produto:
        produto = Produto(**payload.model_dump())
        self.db.add(produto)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def get_by_id(self, produto_id: int) -> Produto | None:
        return self.db.get(Produto, produto_id)

    def delete(self, produto: Produto) -> None:
        self.db.delete(produto)
        self.db.commit()

    def update(self, produto: Produto, payload: ProdutoUpdate) -> Produto:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(produto, field, value)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def _apply_filters(self, query, params: ProdutoQueryParams):
        if params.nome:
            query = query.where(Produto.nome.ilike(f"%{params.nome.strip()}%"))
        if params.ativo is not None:
            query = query.where(Produto.ativo.is_(params.ativo))
        return query

    def _apply_sort(self, query, sort: SortField, order: str):
        column_map = {
            "nome": Produto.nome,
            "preco": Produto.preco,
            "estoque": Produto.estoque,
            "id": Produto.id,
            "created_at": Produto.created_at,
        }
        column = column_map[sort]
        ordering = desc(column) if order == "desc" else asc(column)
        return query.order_by(ordering)

    def list_all(self, params: ProdutoQueryParams) -> tuple[list[Produto], int]:
        base_query = select(Produto)
        base_query = self._apply_filters(base_query, params)

        count_query = select(func.count()).select_from(base_query.subquery())
        total = self.db.scalar(count_query) or 0

        query = self._apply_sort(base_query, params.sort, params.order)
        query = query.offset(params.offset).limit(params.limit)
        items = list(self.db.scalars(query).all())
        return items, total

    def get_stats(self) -> dict:
        """Agrega métricas do catálogo — usado pelo endpoint /produtos/stats."""
        total = self.db.scalar(select(func.count(Produto.id))) or 0
        ativos = self.db.scalar(select(func.count(Produto.id)).where(Produto.ativo.is_(True))) or 0
        inativos = total - ativos
        estoque_total = self.db.scalar(select(func.coalesce(func.sum(Produto.estoque), 0))) or 0
        preco_medio = self.db.scalar(select(func.coalesce(func.avg(Produto.preco), 0.0))) or 0.0
        preco_minimo = self.db.scalar(select(func.min(Produto.preco)))
        preco_maximo = self.db.scalar(select(func.max(Produto.preco)))

        return {
            "total_produtos": total,
            "produtos_ativos": ativos,
            "produtos_inativos": inativos,
            "estoque_total": int(estoque_total),
            "preco_medio": float(preco_medio),
            "preco_minimo": float(preco_minimo) if preco_minimo is not None else None,
            "preco_maximo": float(preco_maximo) if preco_maximo is not None else None,
        }
