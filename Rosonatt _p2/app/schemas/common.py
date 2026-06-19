"""Schemas de resposta padronizada."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Envelope padrão para respostas de sucesso."""

    success: bool = True
    data: T


class ErrorResponse(BaseModel):
    """Envelope padrão para respostas de erro."""

    success: bool = False
    message: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Payload simples com mensagem informativa."""

    message: str


class HealthData(BaseModel):
    """Dados retornados pelo healthcheck."""

    status: str
    app_name: str
    version: str
    environment: str
    database: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "app_name": "Produtos API",
                "version": "1.0.0",
                "environment": "development",
                "database": "connected",
            }
        }
    )
