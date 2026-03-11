"""Pydantic settings — reads from .env file."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaSettings(BaseSettings):
    base_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    chat_model: str = "qwen2.5:7b"
    temperature: float = 0.1
    context_window: int = 8192

    model_config = SettingsConfigDict(env_prefix="OLLAMA_", env_file=".env", extra="ignore")


class PostgresSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    db: str = "bioinfo_sidecar"
    user: str = "sidecar"
    password: str = "changeme"

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", extra="ignore")


class ArxivSettings(BaseSettings):
    max_results: int = 50
    rate_limit_seconds: float = 3.0

    model_config = SettingsConfigDict(env_prefix="ARXIV_", env_file=".env", extra="ignore")


class GradioSettings(BaseSettings):
    port: int = 7860
    share: bool = False

    model_config = SettingsConfigDict(env_prefix="GRADIO_", env_file=".env", extra="ignore")


class Settings(BaseSettings):
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    arxiv: ArxivSettings = Field(default_factory=ArxivSettings)
    gradio: GradioSettings = Field(default_factory=GradioSettings)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
