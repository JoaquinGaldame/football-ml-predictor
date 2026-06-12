from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.database.repositories import WeatherPayload


class WeatherClient(ABC):
    @abstractmethod
    def fetch_weather(self, external_match_id: str) -> WeatherPayload | None:
        """Return weather data for a specific match when available."""


class MockWeatherClient(WeatherClient):
    WEATHER_BY_MATCH: dict[str, WeatherPayload] = {
        "mock-20240320-bra-fra": WeatherPayload(
            temperature=17.0,
            humidity=61.0,
            wind_speed=12.0,
            rain_probability=20.0,
            source="mock_weather",
            captured_at=datetime(2024, 3, 20, 16, 0),
        ),
        "mock-20240522-fra-arg": WeatherPayload(
            temperature=13.0,
            humidity=74.0,
            wind_speed=15.0,
            rain_probability=55.0,
            source="mock_weather",
            captured_at=datetime(2024, 5, 22, 13, 0),
        ),
        "mock-20240716-arg-fra": WeatherPayload(
            temperature=29.0,
            humidity=80.0,
            wind_speed=9.0,
            rain_probability=35.0,
            source="mock_weather",
            captured_at=datetime(2024, 7, 16, 15, 0),
        ),
    }

    def fetch_weather(self, external_match_id: str) -> WeatherPayload | None:
        return self.WEATHER_BY_MATCH.get(external_match_id)
