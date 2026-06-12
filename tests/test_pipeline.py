from __future__ import annotations

from app.pipelines.daily_update_pipeline import run_daily_update_pipeline


def test_daily_pipeline_runs() -> None:
    result = run_daily_update_pipeline()

    assert result["training_version"]
    assert result["prediction"]["predicted_result"] in {"HOME_WIN", "DRAW", "AWAY_WIN"}
