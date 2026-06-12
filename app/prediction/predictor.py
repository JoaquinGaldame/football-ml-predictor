from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.features.feature_builder import FeatureBuilder
from app.training.model_registry import ModelRegistry


RESULT_MAP = {0: "HOME_WIN", 1: "DRAW", 2: "AWAY_WIN"}


@dataclass(slots=True)
class MatchPredictionInput:
    home_team: str
    away_team: str
    match_date: datetime
    neutral_site: bool = False
    venue: str | None = None
    country: str | None = None


class Predictor:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.feature_builder = FeatureBuilder(session)
        self.registry = ModelRegistry(session)

    def predict(self, payload: MatchPredictionInput) -> dict:
        artifact = self.registry.load_active()
        features = self.feature_builder.build_future_match_features(
            home_team=payload.home_team,
            away_team=payload.away_team,
            match_date=payload.match_date,
            neutral_site=payload.neutral_site,
            venue=payload.venue,
            country=payload.country,
        )
        model = artifact["model"]
        probabilities = model.predict_proba(features)[0]
        predicted_index = int(model.predict(features)[0])
        factors = self._explain(features.iloc[0].to_dict(), payload)
        return {
            "home_team": payload.home_team,
            "away_team": payload.away_team,
            "model_version": artifact["metrics"].get("version") or artifact.get("version"),
            "probabilities": {
                "home_win": round(float(probabilities[0]), 4),
                "draw": round(float(probabilities[1]), 4),
                "away_win": round(float(probabilities[2]), 4),
            },
            "predicted_result": RESULT_MAP[predicted_index],
            "confidence": round(float(max(probabilities)), 4),
            "main_factors": factors,
        }

    def _explain(self, features: dict, payload: MatchPredictionInput) -> list[str]:
        factors: list[str] = []
        rating_diff = float(features.get("rating_diff") or 0.0)
        unavailable_diff = float(features.get("unavailable_players_diff") or 0.0)
        if rating_diff > 0:
            factors.append(f"{payload.home_team} tiene mejor rating Elo")
        elif rating_diff < 0:
            factors.append(f"{payload.away_team} tiene mejor rating Elo")
        if unavailable_diff > 0:
            factors.append(f"{payload.home_team} tiene mas bajas reportadas")
        elif unavailable_diff < 0:
            factors.append(f"{payload.away_team} tiene mas bajas reportadas")
        if payload.neutral_site:
            factors.append("Partido en sede neutral")
        elif int(features.get("home_advantage", 0)) == 1:
            factors.append(f"{payload.home_team} mantiene ventaja de localia")
        if not factors:
            factors.append("Prediccion basada en forma reciente y ratings disponibles")
        return factors[:3]
