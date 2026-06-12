from __future__ import annotations

from app.pipelines.daily_update_pipeline import run_daily_update_pipeline


def run_full_retrain_pipeline() -> dict:
    return run_daily_update_pipeline()


if __name__ == "__main__":
    run_full_retrain_pipeline()
