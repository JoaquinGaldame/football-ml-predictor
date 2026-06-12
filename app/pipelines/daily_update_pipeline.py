from __future__ import annotations

import logging
from datetime import datetime

from app.database.db import init_db, session_scope
from app.database.repositories import TrainingRunRepository
from app.ingestion.ingestion_service import IngestionService
from app.prediction.prediction_service import PredictionService
from app.prediction.predictor import MatchPredictionInput
from app.reports.metrics_report import generate_metrics_report
from app.training.train_model import ModelTrainer


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)


def run_daily_update_pipeline() -> dict:
    init_db()
    with session_scope() as session:
        ingestion = IngestionService(session).run()
        training = ModelTrainer(session).train()
        TrainingRunRepository(session).create(
            model_version=training.artifact.version,
            dataset_size=training.dataset_size,
            accuracy=training.evaluation.accuracy,
            log_loss=training.evaluation.log_loss,
            f1_score=training.evaluation.f1_macro,
            notes="Daily update pipeline run",
        )
        report_path = generate_metrics_report(training)
        prediction = PredictionService(session).predict_and_store(
            MatchPredictionInput(
                home_team="Argentina",
                away_team="France",
                match_date=datetime(2025, 1, 15, 20, 0),
                neutral_site=True,
                venue="Demo Final Venue",
                country="United States",
            )
        )
        result = {
            "ingestion": ingestion,
            "training_version": training.artifact.version,
            "report_path": str(report_path),
            "prediction": prediction,
        }
        logger.info("Daily update pipeline completed with model version=%s", training.artifact.version)
        return result


if __name__ == "__main__":
    run_daily_update_pipeline()
