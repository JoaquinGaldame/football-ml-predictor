from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.features.feature_schema import MatchFeatureRow


FEATURE_COLUMNS = [
    "date_ordinal",
    "rating_diff",
    "home_goals_for_avg_5",
    "away_goals_for_avg_5",
    "home_goals_against_avg_5",
    "away_goals_against_avg_5",
    "form_points_diff",
    "rest_days_diff",
    "home_advantage",
    "neutral_site",
    "unavailable_players_diff",
    "humidity",
    "temperature",
    "wind_speed",
    "rain_probability",
    "xg_diff_avg_5",
    "shots_on_target_diff_avg_5",
    "offensive_strength_diff",
    "defensive_strength_diff",
]


@dataclass(slots=True)
class BuiltDataset:
    dataframe: pd.DataFrame
    feature_columns: list[str]
    target_column: str = "target"


class FeatureBuilder:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.connection = session.connection()

    def build_training_dataset(self) -> BuiltDataset:
        matches = self._load_matches()
        rows: list[dict] = []
        for _, match in matches.iterrows():
            row = self._build_row(matches, match, include_target=True)
            if row is not None:
                rows.append(row.model_dump())
        dataframe = pd.DataFrame(rows)
        return BuiltDataset(dataframe=dataframe, feature_columns=FEATURE_COLUMNS)

    def build_future_match_features(
        self,
        *,
        home_team: str,
        away_team: str,
        match_date: datetime,
        neutral_site: bool = False,
        venue: str | None = None,
        country: str | None = None,
    ) -> pd.DataFrame:
        matches = self._load_matches()
        synthetic_match = pd.Series(
            {
                "id": None,
                "external_id": None,
                "date": pd.Timestamp(match_date),
                "competition": "future_prediction",
                "home_team_name": home_team,
                "away_team_name": away_team,
                "goals_home": None,
                "goals_away": None,
                "neutral_site": neutral_site,
                "venue": venue,
                "country": country,
            }
        )
        row = self._build_row(matches, synthetic_match, include_target=False)
        if row is None:
            raise ValueError("Unable to build features for the requested match")
        return pd.DataFrame([row.model_dump()])[FEATURE_COLUMNS]

    def _build_row(self, matches: pd.DataFrame, match: pd.Series, *, include_target: bool) -> MatchFeatureRow | None:
        prior_matches = matches[matches["date"] < match["date"]]
        home_team = match["home_team_name"]
        away_team = match["away_team_name"]

        home_prior = self._team_history(prior_matches, home_team)
        away_prior = self._team_history(prior_matches, away_team)

        if include_target and (pd.isna(match["goals_home"]) or pd.isna(match["goals_away"])):
            return None
        if include_target and (home_prior.empty or away_prior.empty):
            return None

        weather = self._latest_weather(match["id"])
        rating_diff = self._rating_for_team(home_team, match["date"]) - self._rating_for_team(away_team, match["date"])
        unavailable_diff = self._unavailable_players(home_team) - self._unavailable_players(away_team)

        home_rest = self._rest_days(home_prior, match["date"])
        away_rest = self._rest_days(away_prior, match["date"])
        target = None
        if include_target:
            if match["goals_home"] > match["goals_away"]:
                target = 0
            elif match["goals_home"] == match["goals_away"]:
                target = 1
            else:
                target = 2

        row = MatchFeatureRow(
            match_id=None if pd.isna(match["id"]) else int(match["id"]),
            date_ordinal=pd.Timestamp(match["date"]).toordinal(),
            home_team=home_team,
            away_team=away_team,
            rating_diff=rating_diff,
            home_goals_for_avg_5=self._avg_metric(home_prior, "goals_for"),
            away_goals_for_avg_5=self._avg_metric(away_prior, "goals_for"),
            home_goals_against_avg_5=self._avg_metric(home_prior, "goals_against"),
            away_goals_against_avg_5=self._avg_metric(away_prior, "goals_against"),
            form_points_diff=self._form_points(home_prior) - self._form_points(away_prior),
            rest_days_diff=(home_rest - away_rest) if home_rest is not None and away_rest is not None else None,
            home_advantage=0 if bool(match["neutral_site"]) else 1,
            neutral_site=int(bool(match["neutral_site"])),
            unavailable_players_diff=unavailable_diff,
            humidity=weather.get("humidity"),
            temperature=weather.get("temperature"),
            wind_speed=weather.get("wind_speed"),
            rain_probability=weather.get("rain_probability"),
            xg_diff_avg_5=self._avg_metric(home_prior, "xg") - self._avg_metric(away_prior, "xg"),
            shots_on_target_diff_avg_5=self._avg_metric(home_prior, "shots_on_target") - self._avg_metric(away_prior, "shots_on_target"),
            offensive_strength_diff=self._avg_metric(home_prior, "goals_for") + self._avg_metric(home_prior, "xg") - self._avg_metric(away_prior, "goals_for") - self._avg_metric(away_prior, "xg"),
            defensive_strength_diff=self._avg_metric(away_prior, "goals_against") - self._avg_metric(home_prior, "goals_against"),
            target=target,
        )
        return row

    def _load_matches(self) -> pd.DataFrame:
        query = text(
            """
            SELECT
                m.id,
                m.external_id,
                m.date,
                m.competition,
                m.goals_home,
                m.goals_away,
                m.neutral_site,
                m.venue,
                m.country,
                th.name AS home_team_name,
                ta.name AS away_team_name
            FROM matches m
            JOIN teams th ON th.id = m.team_home_id
            JOIN teams ta ON ta.id = m.team_away_id
            ORDER BY m.date ASC
            """
        )
        return pd.read_sql(query, self.connection, parse_dates=["date"])

    def _team_history(self, matches: pd.DataFrame, team_name: str) -> pd.DataFrame:
        team_matches = matches[
            (matches["home_team_name"] == team_name) | (matches["away_team_name"] == team_name)
        ].copy()
        if team_matches.empty:
            return team_matches
        team_matches["goals_for"] = team_matches.apply(
            lambda row: row["goals_home"] if row["home_team_name"] == team_name else row["goals_away"],
            axis=1,
        )
        team_matches["goals_against"] = team_matches.apply(
            lambda row: row["goals_away"] if row["home_team_name"] == team_name else row["goals_home"],
            axis=1,
        )
        team_matches["result_points"] = team_matches.apply(
            lambda row: 3
            if row["goals_for"] > row["goals_against"]
            else 1
            if row["goals_for"] == row["goals_against"]
            else 0,
            axis=1,
        )
        stats = self._load_stats(team_name)
        if not stats.empty:
            team_matches = team_matches.merge(stats, on="id", how="left")
        else:
            team_matches["shots_on_target"] = None
            team_matches["xg"] = None
        return team_matches.sort_values("date").tail(5)

    def _load_stats(self, team_name: str) -> pd.DataFrame:
        query = text(
            """
            SELECT
                m.id,
                s.shots_on_target,
                s.xg
            FROM team_match_stats s
            JOIN matches m ON m.id = s.match_id
            JOIN teams t ON t.id = s.team_id
            WHERE t.name = :team_name
            """
        )
        return pd.read_sql(query, self.connection, params={"team_name": team_name})

    def _latest_weather(self, match_id: int | None) -> dict[str, float | None]:
        if match_id is None:
            return {"temperature": None, "humidity": None, "wind_speed": None, "rain_probability": None}
        query = text(
            """
            SELECT temperature, humidity, wind_speed, rain_probability
            FROM weather_snapshots
            WHERE match_id = :match_id
            ORDER BY captured_at DESC
            LIMIT 1
            """
        )
        frame = pd.read_sql(query, self.connection, params={"match_id": match_id})
        if frame.empty:
            return {"temperature": None, "humidity": None, "wind_speed": None, "rain_probability": None}
        return frame.iloc[0].to_dict()

    def _rating_for_team(self, team_name: str, match_date: pd.Timestamp) -> float:
        query = text(
            """
            SELECT tr.rating_value
            FROM team_ratings tr
            JOIN teams t ON t.id = tr.team_id
            WHERE t.name = :team_name
              AND tr.rating_date <= :match_date
            ORDER BY tr.rating_date DESC
            LIMIT 1
            """
        )
        frame = pd.read_sql(query, self.connection, params={"team_name": team_name, "match_date": match_date.to_pydatetime()})
        if frame.empty:
            return 0.0
        return float(frame.iloc[0]["rating_value"])

    def _unavailable_players(self, team_name: str) -> int:
        query = text(
            """
            SELECT COUNT(*) AS unavailable_count
            FROM player_status ps
            JOIN teams t ON t.id = ps.team_id
            WHERE t.name = :team_name
              AND LOWER(ps.status) IN ('out', 'injured', 'suspended')
            """
        )
        frame = pd.read_sql(query, self.connection, params={"team_name": team_name})
        if frame.empty:
            return 0
        return int(frame.iloc[0]["unavailable_count"])

    @staticmethod
    def _avg_metric(frame: pd.DataFrame, column: str) -> float:
        if frame.empty or column not in frame:
            return 0.0
        series = pd.to_numeric(frame[column], errors="coerce")
        return float(series.mean()) if not series.dropna().empty else 0.0

    @staticmethod
    def _form_points(frame: pd.DataFrame) -> float:
        if frame.empty or "result_points" not in frame:
            return 0.0
        return float(frame["result_points"].sum())

    @staticmethod
    def _rest_days(frame: pd.DataFrame, match_date: pd.Timestamp) -> float | None:
        if frame.empty:
            return None
        last_match_date = pd.Timestamp(frame.iloc[-1]["date"])
        return float((match_date - last_match_date).days)
