from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "football-ml-predictor"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(
        default=f"sqlite:///{(BASE_DIR / 'data' / 'football.db').as_posix()}",
        alias="DATABASE_URL",
    )
    model_dir: Path = Field(default=BASE_DIR / "models", alias="MODEL_DIR")
    reports_dir: Path = Field(default=BASE_DIR / "reports", alias="REPORTS_DIR")
    default_algorithm: str = Field(default="random_forest", alias="DEFAULT_ALGORITHM")
    random_state: int = Field(default=42, alias="RANDOM_STATE")
    test_size: float = Field(default=0.25, alias="TEST_SIZE")
    min_training_rows: int = Field(default=8, alias="MIN_TRAINING_ROWS")
    enable_mock_ingestion: bool = Field(default=True, alias="ENABLE_MOCK_INGESTION")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    (settings.model_dir / "latest").mkdir(parents=True, exist_ok=True)
    (settings.model_dir / "versions").mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    return settings
