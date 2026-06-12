from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.models import Venue
from app.database.repositories import MatchRepository, PlayerStatusRepository, TeamRatingRepository
from app.ingestion.elo_rating_client import EloRatingClient, MockEloRatingClient, WorldFootballEloClient
from app.ingestion.football_data_client import FootballDataClient
from app.ingestion.match_data_client import FootballDataMatchDataClient, MatchDataClient, MockMatchDataClient
from app.ingestion.open_meteo_client import OpenMeteoClient
from app.ingestion.player_status_provider import (
    MockPlayerStatusProvider,
    PlaceholderPaidPlayerStatusProvider,
    PlayerStatusProvider,
)
from app.ingestion.weather_client import MockWeatherClient, OpenMeteoWeatherClient, WeatherClient


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionResult:
    matches_processed: int
    player_status_records: int
    ratings_processed: int
    competitions_processed: int = 0
    teams_processed: int = 0
    weather_processed: int = 0


class IngestionService:
    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        match_client: MatchDataClient | None = None,
        player_status_provider: PlayerStatusProvider | None = None,
        weather_client: WeatherClient | None = None,
        rating_client: EloRatingClient | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.match_client = match_client or self._build_match_client()
        self.player_status_provider = player_status_provider or self._build_player_status_provider()
        self.weather_client = weather_client or self._build_weather_client()
        self.rating_client = rating_client or self._build_rating_client()
        self.match_repository = MatchRepository(session)
        self.player_status_repository = PlayerStatusRepository(session)
        self.rating_repository = TeamRatingRepository(session)

    def run(self) -> IngestionResult:
        competitions = self.match_client.fetch_competitions()
        teams = self.match_client.fetch_teams()
        historical_matches = self.match_client.fetch_historical_matches()
        upcoming_matches = self.match_client.fetch_upcoming_matches()

        for team in teams:
            self.match_repository.teams.upsert(team)

        processed = 0
        weather_processed = 0
        match_items = self._deduplicate_matches([*historical_matches, *upcoming_matches])
        for item in match_items:
            match = self.match_repository.upsert_match(item["match"])
            self.match_repository.upsert_team_stats(match, item.get("stats", []))
            venue = self._resolve_venue(item["match"].venue)
            weather_payload = self.weather_client.fetch_weather(
                item["match"].external_id,
                latitude=venue.latitude if venue else None,
                longitude=venue.longitude if venue else None,
                match_datetime=item["match"].date,
            )
            if weather_payload is not None:
                self.match_repository.upsert_weather(match, weather_payload)
                weather_processed += 1
            processed += 1

        known_team_names = sorted(
            {
                item["match"].home_team.name
                for item in match_items
            }
            | {
                item["match"].away_team.name
                for item in match_items
            }
        )
        team_codes_by_name = {
            item["match"].home_team.name: item["match"].home_team.fifa_code
            for item in match_items
        }
        team_codes_by_name.update(
            {
                item["match"].away_team.name: item["match"].away_team.fifa_code
                for item in match_items
            }
        )

        statuses = self.player_status_provider.fetch_statuses(known_team_names) if self.settings.enable_player_status else []
        self.player_status_repository.replace_team_statuses(statuses)

        rating_payloads = self.rating_client.fetch_ratings(
            team_names=known_team_names,
            team_codes_by_name=team_codes_by_name,
            rating_date=datetime.now(timezone.utc),
        )
        self.rating_repository.upsert_many(rating_payloads)

        logger.info(
            "Ingestion completed: competitions=%s teams=%s matches=%s weather=%s player_status=%s ratings=%s",
            len(competitions),
            len(teams),
            processed,
            weather_processed,
            len(statuses),
            len(rating_payloads),
        )
        return IngestionResult(
            matches_processed=processed,
            player_status_records=len(statuses),
            ratings_processed=len(rating_payloads),
            competitions_processed=len(competitions),
            teams_processed=len(teams),
            weather_processed=weather_processed,
        )

    def _deduplicate_matches(self, items: list[dict]) -> list[dict]:
        deduplicated: dict[str, dict] = {}
        for item in items:
            deduplicated[item["match"].external_id] = item
        return list(deduplicated.values())

    def _resolve_venue(self, venue_name: str | None) -> Venue | None:
        if not venue_name:
            return None
        return self.match_repository.venues.get_by_name(venue_name)

    def _build_match_client(self) -> MatchDataClient:
        if self.settings.enable_real_ingestion:
            return FootballDataMatchDataClient(
                FootballDataClient(
                    api_key=self.settings.football_data_api_key or "",
                    base_url=self.settings.football_data_base_url,
                    timeout=self.settings.request_timeout_seconds,
                ),
                settings=self.settings,
            )
        return MockMatchDataClient()

    def _build_weather_client(self) -> WeatherClient:
        if self.settings.enable_real_ingestion:
            return OpenMeteoWeatherClient(
                OpenMeteoClient(
                    forecast_url=self.settings.open_meteo_forecast_url,
                    historical_url=self.settings.open_meteo_historical_url,
                    timeout=self.settings.request_timeout_seconds,
                )
            )
        return MockWeatherClient()

    def _build_rating_client(self) -> EloRatingClient:
        if self.settings.enable_real_ingestion:
            return WorldFootballEloClient(
                ratings_url=self.settings.elo_ratings_url,
                timeout=self.settings.request_timeout_seconds,
            )
        return MockEloRatingClient()

    def _build_player_status_provider(self) -> PlayerStatusProvider:
        if self.settings.enable_player_status:
            return PlaceholderPaidPlayerStatusProvider()
        return MockPlayerStatusProvider()
