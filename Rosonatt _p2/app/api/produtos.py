"""Endpoints de gerenciamento de produtos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.database import get_produto_service
from app.schemas.common import SuccessResponse
from app.schemas.produto import (
    ProdutoCreate,
    ProdutoListData,
    ProdutoQueryParams,
    ProdutoResponse,
    ProdutoStatsData,
    ProdutoUpdate,
    SortField,
    SortOrder,
)
from app.services.produto_service import ProdutoService

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def get_query_params(
    nome: Annotated[str | None, Query(description="Filtra produtos pelo nome (busca parcial)")] = None,
    ativo: Annotated[bool | None, Query(description="Filtra por status ativo/inativo")] = None,
    page: Annotated[int, Query(ge=1, description="Número da página")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Itens por página")] = 10,
    sort: Annotated[SortField, Query(description="Campo de ordenação")] = "id",
    order: Annotated[SortOrder, Query(description="Direção da ordenação")] = "asc",
) -> ProdutoQueryParams:
    return ProdutoQueryParams(
        nome=nome,
        ativo=ativo,
        page=page,
        limit=limit,
        sort=sort,
        order=order,
    )


@router.get(
    "/stats",
    response_model=SuccessResponse[ProdutoStatsData],
    summary="Estatísticas agregadas do catálogo",
)
def obter_estatisticas(
    service: ProdutoService = Depends(get_produto_service),
) -> SuccessResponse[ProdutoStatsData]:
    # Futuramente este endpoint pode ser integrado a um dashboard de vendas.
    return SuccessResponse(data=service.get_stats())


@router.get(
    "",
    response_model=SuccessResponse[ProdutoListData],
    summary="Lista produtos com filtros, paginação e ordenação",
)
def listar_produtos(
    params: ProdutoQueryParams = Depends(get_query_params),
    service: ProdutoService = Depends(get_produto_service),
) -> SuccessResponse[ProdutoListData]:
    return SuccessResponse(data=service.list_produtos(params))


@router.post(
    "",
    response_model=SuccessResponse[ProdutoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo produto",
)
def criar_produto(
    payload: ProdutoCreate,
    service: ProdutoService = Depends(get_produto_service),
) -> SuccessResponse[ProdutoResponse]:
    return SuccessResponse(data=service.create_produto(payload))


@router.get(
    "/{produto_id}",
    response_model=SuccessResponse[ProdutoResponse],
    summary="Busca produto por ID",
)
def buscar_produto(
    produto_id: int,
    service: ProdutoService = Depends(get_produto_service),
) -> SuccessResponse[ProdutoResponse]:
    return SuccessResponse(data=service.get_produto(produto_id))


@router.put(
    "/{produto_id}",
    response_model=SuccessResponse[ProdutoResponse],
    summary="Atualiza um produto existente",
)
def atualizar_produto(
    produto_id: int,
    payload: ProdutoUpdate,
    service: ProdutoService = Depends(get_produto_service),
) -> SuccessResponse[ProdutoResponse]:
    return SuccessResponse(data=service.update_produto(produto_id, payload))


@router.patch(
    "/{produto_id}",
    response_model=SuccessResponse[ProdutoResponse],
    summary="Atualiza parcialmente um produto",
)
def atualizar_produto_parcial(
    produto_id: int,
    payload: ProdutoUpdate,
    service: ProdutoService = Depends(get_produto_service),
) -> SuccessResponse[ProdutoResponse]:
    return SuccessResponse(data=service.update_produto(produto_id, payload))


@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um produto do catálogo",
)
def remover_produto(
    produto_id: int,
    service: ProdutoService = Depends(get_produto_service),
) -> Response:
    service.delete_produto(produto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
