from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.database.repositories import PlayerStatusPayload


class PlayerStatusClient(ABC):
    @abstractmethod
    def fetch_statuses(self) -> list[PlayerStatusPayload]:
        """Return player availability data."""


class MockPlayerStatusClient(PlayerStatusClient):
    def fetch_statuses(self) -> list[PlayerStatusPayload]:
        now = datetime(2024, 12, 1, 10, 0)
        return [
            PlayerStatusPayload(
                team_name="France",
                player_name="Theo Hernandez",
                status="out",
                reason="hamstring",
                source="mock_feed",
                reported_at=now,
            ),
            PlayerStatusPayload(
                team_name="Brazil",
                player_name="Vinicius Junior",
                status="questionable",
                reason="fatigue",
                source="mock_feed",
                reported_at=now,
            ),
            PlayerStatusPayload(
                team_name="Spain",
                player_name="Pedri",
                status="out",
                reason="ankle",
                source="mock_feed",
                reported_at=now,
            ),
        ]
