from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.repositories import ModelRegistryRepository


@dataclass(slots=True)
class StoredModelArtifact:
    version: str
    version_path: Path
    latest_path: Path


class ModelRegistry:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ModelRegistryRepository(session)
        self.settings = get_settings()

    def store(self, *, artifact: dict, algorithm: str, metrics: dict) -> StoredModelArtifact:
        version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        version_path = self.settings.model_dir / "versions" / f"model_{version}.pkl"
        latest_path = self.settings.model_dir / "latest" / "model.pkl"
        artifact_to_store = {**artifact, "version": version, "metrics": {**metrics, "version": version}}
        joblib.dump(artifact_to_store, version_path)
        joblib.dump(artifact_to_store, latest_path)
        self.repository.activate_version(version, str(version_path), algorithm, artifact_to_store["metrics"])
        return StoredModelArtifact(version=version, version_path=version_path, latest_path=latest_path)

    def load_active(self) -> dict:
        model_version = self.repository.get_active()
        if model_version is None:
            latest_path = self.settings.model_dir / "latest" / "model.pkl"
            if not latest_path.exists():
                raise FileNotFoundError("No active model found in registry or latest path")
            return joblib.load(latest_path)
        return joblib.load(model_version.file_path)
