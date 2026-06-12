from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database.models import (
    Match,
    ModelVersion,
    PlayerStatus,
    Prediction,
    Team,
    TeamMatchStats,
    TeamRating,
    TrainingRun,
    Venue,
    WeatherSnapshot,
)


@dataclass(slots=True)
class TeamPayload:
    name: str
    country: str | None = None
    fifa_code: str | None = None


@dataclass(slots=True)
class MatchPayload:
    external_id: str
    date: datetime
    competition: str | None
    home_team: TeamPayload
    away_team: TeamPayload
    goals_home: int | None = None
    goals_away: int | None = None
    neutral_site: bool = False
    venue: str | None = None
    country: str | None = None
    venue_data: "VenuePayload | None" = None


@dataclass(slots=True)
class TeamStatsPayload:
    team_name: str
    shots: int | None = None
    shots_on_target: int | None = None
    possession: float | None = None
    xg: float | None = None
    corners: int | None = None
    fouls: int | None = None


@dataclass(slots=True)
class PlayerStatusPayload:
    team_name: str
    player_name: str
    status: str
    reason: str | None
    source: str | None
    reported_at: datetime


@dataclass(slots=True)
class VenuePayload:
    name: str
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str | None = None


@dataclass(slots=True)
class WeatherPayload:
    temperature: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    rain_probability: float | None = None
    source: str | None = None
    captured_at: datetime | None = None


@dataclass(slots=True)
class TeamRatingPayload:
    team_name: str
    rating_type: str
    rating_value: float
    rating_date: datetime
    source: str | None


class TeamRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, payload: TeamPayload) -> Team:
        team = self.session.scalar(select(Team).where(Team.name == payload.name))
        if team is None:
            team = Team(name=payload.name, country=payload.country, fifa_code=payload.fifa_code)
            self.session.add(team)
            self.session.flush()
            return team

        team.country = payload.country or team.country
        team.fifa_code = payload.fifa_code or team.fifa_code
        self.session.flush()
        return team

    def get_by_name(self, name: str) -> Team | None:
        return self.session.scalar(select(Team).where(Team.name == name))


class VenueRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, payload: VenuePayload) -> Venue:
        venue = self.session.scalar(select(Venue).where(Venue.name == payload.name))
        if venue is None:
            venue = Venue(
                name=payload.name,
                city=payload.city,
                country=payload.country,
                latitude=payload.latitude,
                longitude=payload.longitude,
                source=payload.source,
            )
            self.session.add(venue)
            self.session.flush()
            return venue

        venue.city = payload.city or venue.city
        venue.country = payload.country or venue.country
        venue.latitude = payload.latitude if payload.latitude is not None else venue.latitude
        venue.longitude = payload.longitude if payload.longitude is not None else venue.longitude
        venue.source = payload.source or venue.source
        self.session.flush()
        return venue

    def get_by_name(self, name: str) -> Venue | None:
        return self.session.scalar(select(Venue).where(Venue.name == name))


class MatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.teams = TeamRepository(session)
        self.venues = VenueRepository(session)

    def upsert_match(self, payload: MatchPayload) -> Match:
        home_team = self.teams.upsert(payload.home_team)
        away_team = self.teams.upsert(payload.away_team)
        venue_row = None
        if payload.venue_data is not None:
            venue_row = self.venues.upsert(payload.venue_data)
        elif payload.venue:
            venue_row = self.venues.upsert(VenuePayload(name=payload.venue, country=payload.country))
        match = self.session.scalar(select(Match).where(Match.external_id == payload.external_id))
        if match is None:
            match = Match(
                external_id=payload.external_id,
                date=payload.date,
                competition=payload.competition,
                team_home_id=home_team.id,
                team_away_id=away_team.id,
                goals_home=payload.goals_home,
                goals_away=payload.goals_away,
                neutral_site=payload.neutral_site,
                venue_id=venue_row.id if venue_row else None,
                venue=payload.venue,
                country=payload.country,
            )
            self.session.add(match)
            self.session.flush()
            return match

        match.date = payload.date
        match.competition = payload.competition
        match.team_home_id = home_team.id
        match.team_away_id = away_team.id
        match.goals_home = payload.goals_home
        match.goals_away = payload.goals_away
        match.neutral_site = payload.neutral_site
        match.venue_id = venue_row.id if venue_row else match.venue_id
        match.venue = payload.venue
        match.country = payload.country
        self.session.flush()
        return match

    def upsert_team_stats(self, match: Match, stats_payloads: Sequence[TeamStatsPayload]) -> None:
        for payload in stats_payloads:
            team = self.teams.get_by_name(payload.team_name)
            if team is None:
                raise ValueError(f"Unknown team for stats payload: {payload.team_name}")
            row = self.session.scalar(
                select(TeamMatchStats).where(
                    TeamMatchStats.match_id == match.id,
                    TeamMatchStats.team_id == team.id,
                )
            )
            if row is None:
                row = TeamMatchStats(match_id=match.id, team_id=team.id)
                self.session.add(row)
            row.shots = payload.shots
            row.shots_on_target = payload.shots_on_target
            row.possession = payload.possession
            row.xg = payload.xg
            row.corners = payload.corners
            row.fouls = payload.fouls
        self.session.flush()

    def upsert_weather(self, match: Match, payload: WeatherPayload | None) -> None:
        if payload is None:
            return
        query = select(WeatherSnapshot).where(WeatherSnapshot.match_id == match.id)
        if payload.source:
            query = query.where(WeatherSnapshot.source == payload.source)
        snapshot = self.session.scalar(query)
        if snapshot is None:
            snapshot = WeatherSnapshot(match_id=match.id)
            self.session.add(snapshot)
        snapshot.temperature = payload.temperature
        snapshot.humidity = payload.humidity
        snapshot.wind_speed = payload.wind_speed
        snapshot.rain_probability = payload.rain_probability
        snapshot.source = payload.source
        snapshot.captured_at = payload.captured_at or datetime.now(timezone.utc)
        self.session.flush()

    def list_matches(self) -> list[Match]:
        return list(self.session.scalars(select(Match).order_by(Match.date.asc())))


class PlayerStatusRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.teams = TeamRepository(session)

    def replace_team_statuses(self, payloads: Iterable[PlayerStatusPayload]) -> None:
        grouped: dict[int, list[PlayerStatusPayload]] = {}
        for payload in payloads:
            team = self.teams.get_by_name(payload.team_name)
            if team is None:
                team = self.teams.upsert(TeamPayload(name=payload.team_name))
            grouped.setdefault(team.id, []).append(payload)

        for team_id, team_payloads in grouped.items():
            self.session.query(PlayerStatus).filter(PlayerStatus.team_id == team_id).delete()
            for payload in team_payloads:
                self.session.add(
                    PlayerStatus(
                        team_id=team_id,
                        player_name=payload.player_name,
                        status=payload.status,
                        reason=payload.reason,
                        source=payload.source,
                        reported_at=payload.reported_at,
                    )
                )
        self.session.flush()


class TeamRatingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.teams = TeamRepository(session)

    def upsert_many(self, payloads: Iterable[TeamRatingPayload]) -> None:
        for payload in payloads:
            team = self.teams.get_by_name(payload.team_name)
            if team is None:
                team = self.teams.upsert(TeamPayload(name=payload.team_name))
            rating = self.session.scalar(
                select(TeamRating).where(
                    TeamRating.team_id == team.id,
                    TeamRating.rating_type == payload.rating_type,
                    TeamRating.rating_date == payload.rating_date,
                )
            )
            if rating is None:
                rating = TeamRating(
                    team_id=team.id,
                    rating_type=payload.rating_type,
                    rating_date=payload.rating_date,
                )
                self.session.add(rating)
            rating.rating_value = payload.rating_value
            rating.source = payload.source
        self.session.flush()


class ModelRegistryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def activate_version(self, version: str, file_path: str, algorithm: str, metrics_json: dict) -> ModelVersion:
        self.session.execute(update(ModelVersion).values(is_active=False))
        model_version = self.session.scalar(select(ModelVersion).where(ModelVersion.version == version))
        if model_version is None:
            model_version = ModelVersion(
                version=version,
                file_path=file_path,
                algorithm=algorithm,
                metrics_json=metrics_json,
                is_active=True,
            )
            self.session.add(model_version)
        else:
            model_version.file_path = file_path
            model_version.algorithm = algorithm
            model_version.metrics_json = metrics_json
            model_version.is_active = True
        self.session.flush()
        return model_version

    def get_active(self) -> ModelVersion | None:
        return self.session.scalar(select(ModelVersion).where(ModelVersion.is_active.is_(True)))


class TrainingRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        model_version: str,
        dataset_size: int,
        accuracy: float,
        log_loss: float,
        f1_score: float,
        notes: str | None,
    ) -> TrainingRun:
        row = TrainingRun(
            model_version=model_version,
            dataset_size=dataset_size,
            accuracy=accuracy,
            log_loss=log_loss,
            f1_score=f1_score,
            notes=notes,
        )
        self.session.add(row)
        self.session.flush()
        return row


class PredictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        match_id: int | None,
        model_version: str,
        predicted_home_win: float,
        predicted_draw: float,
        predicted_away_win: float,
        predicted_result: str,
    ) -> Prediction:
        row = Prediction(
            match_id=match_id,
            model_version=model_version,
            predicted_home_win=predicted_home_win,
            predicted_draw=predicted_draw,
            predicted_away_win=predicted_away_win,
            predicted_result=predicted_result,
        )
        self.session.add(row)
        self.session.flush()
        return row
