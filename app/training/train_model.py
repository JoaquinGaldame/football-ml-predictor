from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.features.feature_builder import FeatureBuilder
from app.training.evaluate_model import EvaluationResult, evaluate_predictions
from app.training.model_registry import ModelRegistry, StoredModelArtifact


logger = logging.getLogger(__name__)

try:
    from xgboost import XGBClassifier  # type: ignore
except ImportError:  # pragma: no cover
    XGBClassifier = None


@dataclass(slots=True)
class TrainingOutput:
    artifact: StoredModelArtifact
    evaluation: EvaluationResult
    dataset_size: int
    algorithm: str


class ModelTrainer:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.feature_builder = FeatureBuilder(session)
        self.registry = ModelRegistry(session)

    def train(self) -> TrainingOutput:
        dataset = self.feature_builder.build_training_dataset()
        if dataset.dataframe.empty or len(dataset.dataframe) < self.settings.min_training_rows:
            raise ValueError(
                f"Not enough rows to train. Required={self.settings.min_training_rows} available={len(dataset.dataframe)}"
            )

        train_df, test_df = self._temporal_split(dataset.dataframe)
        X_train = train_df[dataset.feature_columns]
        y_train = train_df[dataset.target_column].astype(int)
        X_test = test_df[dataset.feature_columns]
        y_test = test_df[dataset.target_column].astype(int)

        algorithm, estimator = self._build_estimator()
        model = Pipeline(
            steps=[
                (
                    "preprocess",
                    ColumnTransformer(
                        transformers=[
                            (
                                "num",
                                Pipeline(
                                    steps=[
                                        ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
                                        ("scaler", StandardScaler()),
                                    ]
                                ),
                                dataset.feature_columns,
                            )
                        ]
                    ),
                ),
                ("classifier", estimator),
            ]
        )
        model.fit(X_train, y_train)

        probabilities = model.predict_proba(X_test)
        predicted = model.predict(X_test)
        evaluation = evaluate_predictions(y_test.to_numpy(), probabilities, predicted)
        metrics = {
            "accuracy": evaluation.accuracy,
            "log_loss": evaluation.log_loss,
            "f1_macro": evaluation.f1_macro,
            "classification_report": evaluation.classification_report,
            "train_size": len(train_df),
            "test_size": len(test_df),
        }
        stored = self.registry.store(
            artifact={
                "model": model,
                "feature_columns": dataset.feature_columns,
                "algorithm": algorithm,
                "metrics": metrics,
            },
            algorithm=algorithm,
            metrics=metrics,
        )
        logger.info("Training finished with algorithm=%s version=%s", algorithm, stored.version)
        return TrainingOutput(
            artifact=stored,
            evaluation=evaluation,
            dataset_size=len(dataset.dataframe),
            algorithm=algorithm,
        )

    def _build_estimator(self):
        if XGBClassifier is not None:
            return (
                "xgboost",
                XGBClassifier(
                    n_estimators=120,
                    max_depth=4,
                    learning_rate=0.08,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    objective="multi:softprob",
                    num_class=3,
                    eval_metric="mlogloss",
                    random_state=self.settings.random_state,
                ),
            )
        return (
            "random_forest",
            RandomForestClassifier(
                n_estimators=250,
                max_depth=8,
                min_samples_leaf=2,
                random_state=self.settings.random_state,
            ),
        )

    def _temporal_split(self, dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        sorted_df = dataframe.sort_values("date_ordinal").reset_index(drop=True)
        split_index = max(1, int(np.floor(len(sorted_df) * (1 - self.settings.test_size))))
        split_index = min(split_index, len(sorted_df) - 1)
        return sorted_df.iloc[:split_index].copy(), sorted_df.iloc[split_index:].copy()
