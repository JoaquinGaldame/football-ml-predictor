from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.training.train_model import TrainingOutput


def generate_metrics_report(training_output: TrainingOutput) -> Path:
    settings = get_settings()
    report_path = settings.reports_dir / f"metrics_{training_output.artifact.version}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": training_output.artifact.version,
        "algorithm": training_output.algorithm,
        "dataset_size": training_output.dataset_size,
        "accuracy": training_output.evaluation.accuracy,
        "log_loss": training_output.evaluation.log_loss,
        "f1_macro": training_output.evaluation.f1_macro,
        "classification_report": training_output.evaluation.classification_report,
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_path
