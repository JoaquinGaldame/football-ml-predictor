from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Callable

import httpx

from app.database.repositories import MatchPayload, TeamPayload, VenuePayload


logger = logging.getLogger(__name__)


class FootballDataClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float = 15.0,
        max_retries: int = 3,
        sleeper: Callable[[float], None] = time.sleep,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY is required for real ingestion")
        self.max_retries = max_retries
        self.sleeper = sleeper
        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-Auth-Token": api_key},
            timeout=timeout,
            transport=transport,
        )

    def get_competitions(self) -> list[dict]:
        payload = self._request_json("/competitions")
        return list(payload.get("competitions", []))

    def get_competition_matches(
        self,
        competition_code: str,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
    ) -> list[dict]:
        params: dict[str, str] = {}
        if date_from is not None:
            params["dateFrom"] = date_from.date().isoformat()
        if date_to is not None:
            params["dateTo"] = date_to.date().isoformat()
        if status:
            params["status"] = status
        try:
            payload = self._request_json(f"/competitions/{competition_code}/matches", params=params or None)
        except RuntimeError as exc:
            if params:
                logger.warning(
                    "football-data.org rejected filtered match query for competition=%s params=%s; retrying without filters",
                    competition_code,
                    params,
                )
                payload = self._request_json(f"/competitions/{competition_code}/matches")
            else:
                raise exc
        return [self.normalize_match(match) for match in payload.get("matches", [])]

    def get_team_matches(
        self,
        team_id: int,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
    ) -> list[dict]:
        params: dict[str, str] = {}
        if date_from is not None:
            params["dateFrom"] = date_from.date().isoformat()
        if date_to is not None:
            params["dateTo"] = date_to.date().isoformat()
        if status:
            params["status"] = status
        payload = self._request_json(f"/teams/{team_id}/matches", params=params)
        return [self.normalize_match(match) for match in payload.get("matches", [])]

    def get_team(self, team_id: int) -> TeamPayload:
        payload = self._request_json(f"/teams/{team_id}")
        return self.normalize_team(payload)

    def normalize_team(self, raw_team: dict) -> TeamPayload:
        area = raw_team.get("area") or {}
        return TeamPayload(
            name=raw_team.get("shortName") or raw_team.get("name") or str(raw_team.get("id")),
            country=area.get("name"),
            fifa_code=raw_team.get("tla"),
        )

    def normalize_match(self, raw_match: dict) -> dict:
        home_team = self.normalize_team(raw_match.get("homeTeam") or {})
        away_team = self.normalize_team(raw_match.get("awayTeam") or {})
        score = raw_match.get("score") or {}
        full_time = score.get("fullTime") or {}
        venue_name = (
            raw_match.get("venue")
            or (raw_match.get("homeTeam") or {}).get("venue")
            or (raw_match.get("area") or {}).get("name")
        )
        country = (
            (raw_match.get("area") or {}).get("name")
            or (raw_match.get("homeTeam") or {}).get("area", {}).get("name")
        )
        venue_payload = VenuePayload(
            name=venue_name,
            city=(raw_match.get("homeTeam") or {}).get("address"),
            country=country,
            source="football_data",
        ) if venue_name else None
        return {
            "match": MatchPayload(
                external_id=str(raw_match["id"]),
                date=self._parse_datetime(raw_match["utcDate"]),
                competition=(raw_match.get("competition") or {}).get("name")
                or (raw_match.get("competition") or {}).get("code"),
                home_team=home_team,
                away_team=away_team,
                goals_home=full_time.get("home"),
                goals_away=full_time.get("away"),
                neutral_site=False,
                venue=venue_name,
                country=country,
                venue_data=venue_payload,
            ),
            "stats": [],
        }

    def _request_json(self, path: str, params: dict[str, str] | None = None) -> dict:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            response = self.client.get(path, params=params)
            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = float(response.headers.get("Retry-After", "1"))
                logger.warning("football-data.org rate limited, retrying in %s seconds", retry_after)
                self.sleeper(retry_after)
                continue
            try:
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if 500 <= response.status_code < 600 and attempt < self.max_retries:
                    self.sleeper(1.0)
                    continue
                break
            except httpx.HTTPError as exc:
                last_error = exc
                break
        detail = ""
        if isinstance(last_error, httpx.HTTPStatusError):
            try:
                detail = f" status={last_error.response.status_code} body={last_error.response.text[:300]}"
            except Exception:
                detail = f" status={last_error.response.status_code}"
        raise RuntimeError(f"football-data request failed for {path}{detail}") from last_error

    @staticmethod
    def _parse_datetime(raw_value: str) -> datetime:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
