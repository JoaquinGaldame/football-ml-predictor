from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from io import StringIO

import httpx
import pandas as pd

from app.database.repositories import TeamRatingPayload


TEAM_NAME_ALIASES = {
    "argentina": "Argentina",
    "brazil": "Brazil",
    "france": "France",
    "spain": "Spain",
    "usa": "United States",
}


class EloRatingClient(ABC):
    @abstractmethod
    def fetch_ratings(
        self,
        *,
        team_names: list[str] | None = None,
        team_codes_by_name: dict[str, str | None] | None = None,
        rating_date: datetime | None = None,
    ) -> list[TeamRatingPayload]:
        """Return normalized ratings for the requested teams."""


class MockEloRatingClient(EloRatingClient):
    def fetch_ratings(
        self,
        *,
        team_names: list[str] | None = None,
        team_codes_by_name: dict[str, str | None] | None = None,
        rating_date: datetime | None = None,
    ) -> list[TeamRatingPayload]:
        raw = [
            ("Argentina", 1985.0),
            ("France", 1940.0),
            ("Spain", 1910.0),
            ("Brazil", 1895.0),
        ]
        rating_dates = [
            datetime(2024, 1, 1),
            datetime(2024, 4, 1),
            datetime(2024, 7, 1),
            datetime(2024, 10, 1),
        ]
        allowed = set(team_names or [])
        payloads: list[TeamRatingPayload] = []
        for current_date in rating_dates:
            for index, (team_name, base_rating) in enumerate(raw):
                if allowed and team_name not in allowed:
                    continue
                payloads.append(
                    TeamRatingPayload(
                        team_name=team_name,
                        rating_type="elo",
                        rating_value=base_rating + (current_date.month * 2) - index * 3,
                        rating_date=current_date,
                        source="mock_elo_feed",
                    )
                )
        return payloads


class WorldFootballEloClient(EloRatingClient):
    def __init__(
        self,
        *,
        ratings_url: str,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.ratings_url = ratings_url
        self.timeout = timeout
        self.transport = transport

    def fetch_ratings(
        self,
        *,
        team_names: list[str] | None = None,
        team_codes_by_name: dict[str, str | None] | None = None,
        rating_date: datetime | None = None,
    ) -> list[TeamRatingPayload]:
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            response = client.get(self.ratings_url)
            response.raise_for_status()
        frame = self._parse_table(response.text)
        normalized = []
        code_lookup = {name: code for name, code in (team_codes_by_name or {}).items() if code}
        name_by_code = {code.upper(): name for name, code in code_lookup.items()}
        requested = {self._normalize_team_name(name) for name in (team_names or [])}
        effective_date = rating_date or datetime.now(timezone.utc)
        for _, row in frame.iterrows():
            raw_team_name = str(row["team_name"]).strip()
            raw_team_code = str(row.get("team_code", "")).strip().upper()
            team_name = name_by_code.get(raw_team_code, self._normalize_team_name(raw_team_name))
            if requested and team_name not in requested:
                continue
            rating_value = row["rating_value"]
            if pd.isna(rating_value):
                continue
            normalized.append(
                TeamRatingPayload(
                    team_name=team_name,
                    rating_type="elo",
                    rating_value=float(rating_value),
                    rating_date=effective_date,
                    source="world_football_elo",
                )
            )
        return normalized

    def _parse_table(self, raw_text: str) -> pd.DataFrame:
        headerless = pd.read_csv(StringIO(raw_text), sep="\t", header=None)
        if headerless.shape[1] >= 4:
            parsed = headerless.rename(columns={3: "rating_value"}).copy()
            parsed["team_code"] = parsed[2].astype(str).str.strip().str.upper()
            parsed["team_name"] = parsed["team_code"]
            return parsed
        candidates = [("\t",), (",",)]
        for separator, in candidates:
            frame = pd.read_csv(StringIO(raw_text), sep=separator)
            team_column = self._find_column(frame.columns, ["team", "country", "name"])
            rating_column = self._find_column(frame.columns, ["elo", "rating"])
            if team_column and rating_column:
                code_column = self._find_column(frame.columns, ["code", "abbr", "tla"])
                rename_map = {team_column: "team_name", rating_column: "rating_value"}
                if code_column:
                    rename_map[code_column] = "team_code"
                return frame.rename(columns=rename_map)
        raise ValueError("Unable to parse Elo ratings source")

    @staticmethod
    def _find_column(columns: pd.Index, aliases: list[str]) -> str | None:
        lowered = {str(column).strip().lower(): str(column) for column in columns}
        for alias in aliases:
            for key, original in lowered.items():
                if alias in key:
                    return original
        return None

    @staticmethod
    def _normalize_team_name(team_name: str) -> str:
        cleaned = team_name.strip()
        return TEAM_NAME_ALIASES.get(cleaned.lower(), cleaned)
