from __future__ import annotations

from app.features.feature_builder import FeatureBuilder
from app.ingestion.ingestion_service import IngestionService


def test_feature_builder_creates_training_dataset(session) -> None:
    IngestionService(session).run()
    dataset = FeatureBuilder(session).build_training_dataset()

    assert not dataset.dataframe.empty
    assert set(dataset.feature_columns).issubset(dataset.dataframe.columns)
    assert dataset.target_column in dataset.dataframe.columns
    assert dataset.dataframe["target"].isin([0, 1, 2]).all()
