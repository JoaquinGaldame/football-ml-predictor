from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class MatchFeatureRow(BaseModel):
    match_id: int | None = None
    date_ordinal: int
    home_team: str
    away_team: str
    rating_diff: float | None
    home_goals_for_avg_5: float | None
    away_goals_for_avg_5: float | None
    home_goals_against_avg_5: float | None
    away_goals_against_avg_5: float | None
    form_points_diff: float | None
    rest_days_diff: float | None
    home_advantage: int
    neutral_site: int
    unavailable_players_diff: float | None
    humidity: float | None
    temperature: float | None
    wind_speed: float | None
    rain_probability: float | None
    xg_diff_avg_5: float | None
    shots_on_target_diff_avg_5: float | None
    offensive_strength_diff: float | None
    defensive_strength_diff: float | None
    target: Literal[0, 1, 2] | None = None
