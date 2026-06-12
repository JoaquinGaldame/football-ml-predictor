from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.repositories import PredictionRepository
from app.prediction.predictor import MatchPredictionInput, Predictor


class PredictionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.predictor = Predictor(session)
        self.repository = PredictionRepository(session)

    def predict_and_store(self, payload: MatchPredictionInput, match_id: int | None = None) -> dict:
        response = self.predictor.predict(payload)
        self.repository.create(
            match_id=match_id,
            model_version=response["model_version"] or "latest",
            predicted_home_win=response["probabilities"]["home_win"],
            predicted_draw=response["probabilities"]["draw"],
            predicted_away_win=response["probabilities"]["away_win"],
            predicted_result=response["predicted_result"],
        )
        return response
