from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss


@dataclass(slots=True)
class EvaluationResult:
    accuracy: float
    log_loss: float
    f1_macro: float
    classification_report: dict


def evaluate_predictions(y_true: np.ndarray, probabilities: np.ndarray, predicted_labels: np.ndarray) -> EvaluationResult:
    return EvaluationResult(
        accuracy=float(accuracy_score(y_true, predicted_labels)),
        log_loss=float(log_loss(y_true, probabilities, labels=[0, 1, 2])),
        f1_macro=float(f1_score(y_true, predicted_labels, average="macro")),
        classification_report=classification_report(y_true, predicted_labels, output_dict=True, zero_division=0),
    )
