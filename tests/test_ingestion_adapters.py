from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.config import Settings
from app.database.models import Match
from app.database.repositories import MatchPayload, TeamPayload
from app.features.feature_builder import FeatureBuilder
from app.ingestion.elo_rating_client import EloRatingClient
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.match_data_client import MatchDataClient, MockMatchDataClient
from app.ingestion.player_status_provider import PlaceholderPaidPlayerStatusProvider
from app.ingestion.weather_client import WeatherClient


class SingleMatchClient(MatchDataClient):
    def __init__(self, goals_home: int) -> None:
        self.goals_home = goals_home

    def fetch_historical_matches(self) -> list[dict]:
        return [
            {
                "match": MatchPayload(
                    external_id="real-1",
                    date=datetime(2024, 1, 1, 20, 0),
                    competition="Friendly",
                    home_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    away_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    goals_home=self.goals_home,
                    goals_away=1,
                    neutral_site=False,
                    venue="Monumental",
                    country="Argentina",
                ),
                "stats": [],
            }
        ]

    def fetch_teams(self) -> list[TeamPayload]:
        return [
            TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
            TeamPayload(name="France", country="France", fifa_code="FRA"),
        ]


class EmptyWeatherClient(WeatherClient):
    def fetch_weather(
        self,
        external_match_id: str | None = None,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        match_datetime: datetime | None = None,
    ):
        return None


class EmptyRatingClient(EloRatingClient):
    def fetch_ratings(
        self,
        *,
        team_names: list[str] | None = None,
        team_codes_by_name: dict[str, str | None] | None = None,
        rating_date: datetime | None = None,
    ) -> list:
        return []


def test_ingestion_service_does_not_duplicate_matches(session) -> None:
    settings = Settings(enable_real_ingestion=False, enable_player_status=False)
    service = IngestionService(
        session,
        settings=settings,
        match_client=SingleMatchClient(goals_home=2),
        weather_client=EmptyWeatherClient(),
        rating_client=EmptyRatingClient(),
        player_status_provider=PlaceholderPaidPlayerStatusProvider(),
    )

    service.run()
    service.run()

    assert session.query(Match).count() == 1


def test_ingestion_service_updates_existing_match_result(session) -> None:
    settings = Settings(enable_real_ingestion=False, enable_player_status=False)
    IngestionService(
        session,
        settings=settings,
        match_client=SingleMatchClient(goals_home=1),
        weather_client=EmptyWeatherClient(),
        rating_client=EmptyRatingClient(),
        player_status_provider=PlaceholderPaidPlayerStatusProvider(),
    ).run()
    IngestionService(
        session,
        settings=settings,
        match_client=SingleMatchClient(goals_home=3),
        weather_client=EmptyWeatherClient(),
        rating_client=EmptyRatingClient(),
        player_status_provider=PlaceholderPaidPlayerStatusProvider(),
    ).run()

    match = session.scalar(select(Match).where(Match.external_id == "real-1"))
    assert match is not None
    assert match.goals_home == 3


def test_feature_builder_supports_missing_weather_rating_and_player_status(session) -> None:
    settings = Settings(enable_real_ingestion=False, enable_player_status=False)
    IngestionService(
        session,
        settings=settings,
        match_client=MockMatchDataClient(),
        weather_client=EmptyWeatherClient(),
        rating_client=EmptyRatingClient(),
        player_status_provider=PlaceholderPaidPlayerStatusProvider(),
    ).run()

    dataset = FeatureBuilder(session).build_training_dataset().dataframe

    assert not dataset.empty
    assert dataset["rating_diff"].eq(0.0).all()
    assert dataset["unavailable_players_diff"].eq(0).all()
    assert dataset["temperature"].isna().all()
    assert dataset["humidity"].isna().all()
