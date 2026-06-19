"""Logging estruturado da aplicação."""

import logging
import sys
from typing import Any

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """Formata logs de forma legível para desenvolvimento e observabilidade."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = []
        for key in ("method", "path", "produto_id", "status_code", "detail"):
            if hasattr(record, key):
                extras.append(f"{key}={getattr(record, key)}")
        if extras:
            return f"{base} | {' '.join(extras)}"
        return base


def setup_logging() -> logging.Logger:
    """Configura o logger raiz da aplicação."""
    settings = get_settings()
    logger = logging.getLogger("produtos_api")
    logger.setLevel(settings.log_level.upper())

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            StructuredFormatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    # Evita propagação duplicada para o root logger
    logger.propagate = False
    return logger


def log_with_context(logger: logging.Logger, level: int, message: str, **context: Any) -> None:
    """Registra mensagem com campos extras de contexto."""
    logger.log(level, message, extra=context)
