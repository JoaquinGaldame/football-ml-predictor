from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database.repositories import MatchRepository, PlayerStatusRepository, TeamRatingPayload, TeamRatingRepository
from app.ingestion.match_data_client import MatchDataClient, MockMatchDataClient
from app.ingestion.player_status_client import MockPlayerStatusClient, PlayerStatusClient
from app.ingestion.weather_client import MockWeatherClient, WeatherClient


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionResult:
    matches_processed: int
    player_status_records: int
    ratings_processed: int


class IngestionService:
    def __init__(
        self,
        session: Session,
        match_client: MatchDataClient | None = None,
        player_status_client: PlayerStatusClient | None = None,
        weather_client: WeatherClient | None = None,
    ) -> None:
        self.session = session
        self.match_client = match_client or MockMatchDataClient()
        self.player_status_client = player_status_client or MockPlayerStatusClient()
        self.weather_client = weather_client or MockWeatherClient()
        self.match_repository = MatchRepository(session)
        self.player_status_repository = PlayerStatusRepository(session)
        self.rating_repository = TeamRatingRepository(session)

    def run(self) -> IngestionResult:
        raw_matches = self.match_client.fetch_matches()
        processed = 0
        for item in raw_matches:
            match = self.match_repository.upsert_match(item["match"])
            self.match_repository.upsert_team_stats(match, item.get("stats", []))
            self.match_repository.upsert_weather(match, self.weather_client.fetch_weather(item["match"].external_id))
            processed += 1

        statuses = self.player_status_client.fetch_statuses()
        self.player_status_repository.replace_team_statuses(statuses)

        rating_payloads = self._build_mock_ratings()
        self.rating_repository.upsert_many(rating_payloads)

        logger.info(
            "Ingestion completed: matches=%s player_status=%s ratings=%s",
            processed,
            len(statuses),
            len(rating_payloads),
        )
        return IngestionResult(
            matches_processed=processed,
            player_status_records=len(statuses),
            ratings_processed=len(rating_payloads),
        )

    def _build_mock_ratings(self) -> list[TeamRatingPayload]:
        raw = [
            ("Argentina", 1985.0),
            ("France", 1940.0),
            ("Spain", 1910.0),
            ("Brazil", 1895.0),
        ]
        rating_dates = [
            (2024, 1, 1),
            (2024, 4, 1),
            (2024, 7, 1),
            (2024, 10, 1),
        ]
        payloads: list[TeamRatingPayload] = []
        for year, month, day in rating_dates:
            for index, (team_name, base_rating) in enumerate(raw):
                payloads.append(
                    TeamRatingPayload(
                        team_name=team_name,
                        rating_type="elo",
                        rating_value=base_rating + (month * 2) - index * 3,
                        rating_date=__import__("datetime").datetime(year, month, day),
                        source="mock_elo_feed",
                    )
                )
        return payloads
