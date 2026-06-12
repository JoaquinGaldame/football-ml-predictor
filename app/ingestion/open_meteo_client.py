from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.database.repositories import WeatherPayload


class OpenMeteoClient:
    def __init__(
        self,
        *,
        forecast_url: str,
        historical_url: str,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.forecast_url = forecast_url
        self.historical_url = historical_url
        self.timeout = timeout
        self.transport = transport

    def fetch_weather_at(self, *, latitude: float, longitude: float, match_datetime: datetime) -> WeatherPayload | None:
        if match_datetime.tzinfo is None:
            match_datetime = match_datetime.replace(tzinfo=timezone.utc)
        endpoint = self.forecast_url if match_datetime >= datetime.now(timezone.utc) else self.historical_url
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": match_datetime.date().isoformat(),
            "end_date": match_datetime.date().isoformat(),
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation_probability",
            "timezone": "UTC",
        }
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        return self._parse_hourly_payload(payload, match_datetime)

    def _parse_hourly_payload(self, payload: dict, match_datetime: datetime) -> WeatherPayload | None:
        hourly = payload.get("hourly") or {}
        timeline = hourly.get("time") or []
        if not timeline:
            return None
        target_hour = match_datetime.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        target_iso = target_hour.isoformat().replace("+00:00", "")
        index = next((idx for idx, raw_time in enumerate(timeline) if raw_time.startswith(target_iso)), 0)
        return WeatherPayload(
            temperature=self._pick(hourly.get("temperature_2m"), index),
            humidity=self._pick(hourly.get("relative_humidity_2m"), index),
            wind_speed=self._pick(hourly.get("wind_speed_10m"), index),
            rain_probability=self._pick(hourly.get("precipitation_probability"), index),
            source="open_meteo",
            captured_at=target_hour,
        )

    @staticmethod
    def _pick(values: list[float] | None, index: int) -> float | None:
        if values is None or index >= len(values):
            return None
        value = values[index]
        return None if value is None else float(value)
