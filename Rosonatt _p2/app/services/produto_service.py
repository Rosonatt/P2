"""Serviço de domínio para Produto."""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import log_with_context, setup_logging
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.produto import (
    ProdutoCreate,
    ProdutoListData,
    ProdutoQueryParams,
    ProdutoResponse,
    ProdutoStatsData,
    ProdutoUpdate,
)

logger = setup_logging()


class ProdutoService:
    """Orquestra regras de negócio e delega persistência ao repositório."""

    def __init__(self, db: Session) -> None:
        self.repository = ProdutoRepository(db)

    def list_produtos(self, params: ProdutoQueryParams) -> ProdutoListData:
        items, total = self.repository.list_all(params)
        return ProdutoListData(
            items=[ProdutoResponse.model_validate(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
            pages=params.calculate_pages(total),
        )

    def get_produto(self, produto_id: int) -> ProdutoResponse:
        produto = self.repository.get_by_id(produto_id)
        if produto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com id {produto_id} não encontrado",
            )
        return ProdutoResponse.model_validate(produto)

    def create_produto(self, payload: ProdutoCreate) -> ProdutoResponse:
        produto = self.repository.create(payload)
        log_with_context(
            logger,
            logging.INFO,
            "Produto criado com sucesso",
            produto_id=produto.id,
            method="POST",
            path="/produtos",
        )
        logger.info("Produto criado: id=%s nome=%s", produto.id, produto.nome)
        return ProdutoResponse.model_validate(produto)

    def update_produto(self, produto_id: int, payload: ProdutoUpdate) -> ProdutoResponse:
        produto = self.repository.get_by_id(produto_id)
        if produto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com id {produto_id} não encontrado",
            )
        updated = self.repository.update(produto, payload)
        logger.info("Produto atualizado: id=%s", updated.id)
        return ProdutoResponse.model_validate(updated)

    def delete_produto(self, produto_id: int) -> None:
        produto = self.repository.get_by_id(produto_id)
        if produto is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto com id {produto_id} não encontrado",
            )
        self.repository.delete(produto)
        log_with_context(
            logger,
            logging.INFO,
            "Produto removido com sucesso",
            produto_id=produto_id,
            method="DELETE",
            path=f"/produtos/{produto_id}",
        )
        logger.info("Produto excluído: id=%s", produto_id)

    def get_stats(self) -> ProdutoStatsData:
        stats = self.repository.get_stats()
        return ProdutoStatsData.from_aggregates(**stats)
