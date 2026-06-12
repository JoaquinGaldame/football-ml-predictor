from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.database.repositories import PlayerStatusPayload


class PlayerStatusProvider(ABC):
    @abstractmethod
    def fetch_statuses(self, team_names: list[str] | None = None) -> list[PlayerStatusPayload]:
        """Return normalized player availability data."""


class MockPlayerStatusProvider(PlayerStatusProvider):
    def fetch_statuses(self, team_names: list[str] | None = None) -> list[PlayerStatusPayload]:
        now = datetime(2024, 12, 1, 10, 0)
        statuses = [
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
        if not team_names:
            return statuses
        allowed = set(team_names)
        return [status for status in statuses if status.team_name in allowed]


class PlaceholderPaidPlayerStatusProvider(PlayerStatusProvider):
    def fetch_statuses(self, team_names: list[str] | None = None) -> list[PlayerStatusPayload]:
        return []
