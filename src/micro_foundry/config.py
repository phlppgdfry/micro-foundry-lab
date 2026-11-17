from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )

    foundry_project_endpoint: str | None = None
    foundry_model: str = "gpt-5-mini"
    # "foundry" calls your Foundry model; "offline" answers extractively from the sources,
    # so the lab runs without Azure (CI, first look, cost-free evaluation baseline).
    provider: Literal["foundry", "offline"] = Field(
        default="foundry", alias="MICRO_FOUNDRY_PROVIDER"
    )
    app_allow_origins: str = ""

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.app_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
