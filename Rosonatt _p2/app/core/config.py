"""Configuração centralizada por ambiente."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variáveis de ambiente da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Produtos API"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    database_url: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5432/produtos_dev",
    )
    test_database_url: PostgresDsn = Field(
        default="postgresql://postgres:postgres@localhost:5433/produtos_test",
    )

    # Paginação padrão usada quando o cliente não informa limit
    default_page_size: int = Field(default=10, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=500)

    @field_validator("database_url", "test_database_url", mode="before")
    @classmethod
    def ensure_psycopg_driver(cls, value: str) -> str:
        """Garante compatibilidade com SQLAlchemy 2.x + psycopg3."""
        url = str(value)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def active_database_url(self) -> str:
        """Retorna a URL correta conforme o ambiente de execução."""
        if self.environment == "test":
            return str(self.test_database_url)
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    """Singleton de configuração — evita releitura do .env a cada request."""
    return Settings()
