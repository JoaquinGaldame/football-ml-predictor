from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings
from app.database.db import init_db, session_scope
from app.prediction.prediction_service import PredictionService
from app.prediction.predictor import MatchPredictionInput


app = FastAPI(title=get_settings().app_name)


class PredictionRequest(BaseModel):
    home_team: str
    away_team: str
    match_date: datetime
    neutral_site: bool = False
    venue: str | None = None
    country: str | None = None


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictionRequest) -> dict:
    with session_scope() as session:
        service = PredictionService(session)
        return service.predict_and_store(MatchPredictionInput(**request.model_dump()))
