from __future__ import annotations

from datetime import datetime

from app.ingestion.ingestion_service import IngestionService
from app.prediction.prediction_service import PredictionService
from app.prediction.predictor import MatchPredictionInput
from app.training.train_model import ModelTrainer


def test_prediction_returns_probabilities(session) -> None:
    IngestionService(session).run()
    ModelTrainer(session).train()
    response = PredictionService(session).predict_and_store(
        MatchPredictionInput(
            home_team="Argentina",
            away_team="France",
            match_date=datetime(2025, 1, 10, 20, 0),
            neutral_site=True,
        )
    )

    assert response["predicted_result"] in {"HOME_WIN", "DRAW", "AWAY_WIN"}
    assert response["probabilities"]["home_win"] >= 0.0
    assert len(response["main_factors"]) >= 1
