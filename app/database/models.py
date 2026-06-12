from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.db import Base


class TimestampMixin:
    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(timezone.utc)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class Team(TimestampMixin, Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fifa_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)


class Venue(TimestampMixin, Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Match(TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("external_id", name="uq_matches_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    competition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_home_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    team_away_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    goals_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    neutral_site: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"), nullable=True, index=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)

    home_team: Mapped[Team] = relationship(foreign_keys=[team_home_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[team_away_id])
    venue_ref: Mapped[Venue | None] = relationship(foreign_keys=[venue_id])


class TeamMatchStats(Base):
    __tablename__ = "team_match_stats"
    __table_args__ = (UniqueConstraint("match_id", "team_id", name="uq_team_match_stats_match_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    shots: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_on_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    possession: Mapped[float | None] = mapped_column(Float, nullable=True)
    xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    corners: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fouls: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PlayerStatus(Base):
    __tablename__ = "player_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    player_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=TimestampMixin.utc_now)


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    rain_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=TimestampMixin.utc_now)


class TeamRating(Base):
    __tablename__ = "team_ratings"
    __table_args__ = (UniqueConstraint("team_id", "rating_type", "rating_date", name="uq_team_rating_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    rating_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rating_value: Mapped[float] = mapped_column(Float, nullable=False)
    rating_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"), nullable=True, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    predicted_home_win: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_draw: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_away_win: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_result: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=TimestampMixin.utc_now)


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=TimestampMixin.utc_now)
    dataset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    log_loss: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=TimestampMixin.utc_now)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
