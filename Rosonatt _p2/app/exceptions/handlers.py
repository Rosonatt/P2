"""Handlers globais de exceção para respostas padronizadas."""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.common import ErrorResponse

logger = logging.getLogger("produtos_api")


def register_exception_handlers(app: FastAPI) -> None:
    """Registra handlers globais na aplicação FastAPI."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            field = ".".join(str(item) for item in first_error.get("loc", []) if item != "body")
            message = first_error.get("msg", "Dados inválidos")
            detail = f"{field}: {message}" if field else message
        else:
            detail = "Erro de validação nos dados enviados"

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(message=detail).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        first_error = exc.errors()[0]
        message = first_error.get("msg", "Erro de validação interna")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(message=message).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=message).model_dump(),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        logger.exception("Erro de banco de dados: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                message="Erro ao processar operação no banco de dados",
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Erro inesperado: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                message="Erro interno inesperado. Tente novamente mais tarde.",
            ).model_dump(),
        )
