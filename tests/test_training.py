from __future__ import annotations

from app.ingestion.ingestion_service import IngestionService
from app.training.train_model import ModelTrainer


def test_training_persists_model_artifact(session) -> None:
    IngestionService(session).run()
    output = ModelTrainer(session).train()

    assert output.dataset_size > 0
    assert output.evaluation.accuracy >= 0.0
    assert output.artifact.version_path.exists()
    assert output.artifact.latest_path.exists()
