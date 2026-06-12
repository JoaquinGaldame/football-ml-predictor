from __future__ import annotations

from app.ingestion.ingestion_service import IngestionService
from app.training.model_registry import ModelRegistry
from app.training.train_model import ModelTrainer


def test_model_registry_loads_active_model(session) -> None:
    IngestionService(session).run()
    ModelTrainer(session).train()
    artifact = ModelRegistry(session).load_active()

    assert "model" in artifact
    assert "feature_columns" in artifact
