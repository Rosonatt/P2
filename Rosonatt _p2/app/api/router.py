"""Agregador de rotas da API."""

from fastapi import APIRouter

from app.api import health, produtos

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(produtos.router)
