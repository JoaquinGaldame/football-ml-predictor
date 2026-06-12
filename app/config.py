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
    enable_real_ingestion: bool = Field(default=False, alias="ENABLE_REAL_INGESTION")
    enable_player_status: bool = Field(default=False, alias="ENABLE_PLAYER_STATUS")
    request_timeout_seconds: float = Field(default=15.0, alias="REQUEST_TIMEOUT_SECONDS")
    football_data_api_key: str | None = Field(default=None, alias="FOOTBALL_DATA_API_KEY")
    football_data_base_url: str = Field(default="https://api.football-data.org/v4", alias="FOOTBALL_DATA_BASE_URL")
    football_data_competitions: str = Field(default="WC,EC", alias="FOOTBALL_DATA_COMPETITIONS")
    open_meteo_forecast_url: str = Field(
        default="https://api.open-meteo.com/v1/forecast",
        alias="OPEN_METEO_FORECAST_URL",
    )
    open_meteo_historical_url: str = Field(
        default="https://archive-api.open-meteo.com/v1/archive",
        alias="OPEN_METEO_HISTORICAL_URL",
    )
    elo_ratings_url: str = Field(default="https://www.eloratings.net/World.tsv", alias="ELO_RATINGS_URL")

    @property
    def competition_codes(self) -> list[str]:
        return [code.strip() for code in self.football_data_competitions.split(",") if code.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    (settings.model_dir / "latest").mkdir(parents=True, exist_ok=True)
    (settings.model_dir / "versions").mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    return settings
