from __future__ import annotations

from app.config import get_settings
from app.pipelines.daily_update_pipeline import run_daily_update_pipeline


def test_daily_pipeline_runs() -> None:
    get_settings.cache_clear()
    result = run_daily_update_pipeline()

    assert result["training_version"]
    assert result["prediction"]["predicted_result"] in {"HOME_WIN", "DRAW", "AWAY_WIN"}
    assert get_settings().enable_real_ingestion is False
