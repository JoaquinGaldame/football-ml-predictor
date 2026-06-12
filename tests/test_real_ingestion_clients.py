from __future__ import annotations

from datetime import datetime, timezone

import respx
from httpx import Response

from app.ingestion.football_data_client import FootballDataClient
from app.ingestion.open_meteo_client import OpenMeteoClient


@respx.mock
def test_football_data_client_parses_matches_correctly() -> None:
    respx.get("https://api.football-data.org/v4/competitions/WC/matches").mock(
        return_value=Response(
            200,
            json={
                "matches": [
                    {
                        "id": 99,
                        "utcDate": "2026-06-12T20:00:00Z",
                        "competition": {"code": "WC", "name": "World Cup"},
                        "homeTeam": {
                            "name": "Argentina",
                            "shortName": "Argentina",
                            "tla": "ARG",
                            "area": {"name": "Argentina"},
                        },
                        "awayTeam": {
                            "name": "France",
                            "shortName": "France",
                            "tla": "FRA",
                            "area": {"name": "France"},
                        },
                        "score": {"fullTime": {"home": 2, "away": 1}},
                        "venue": "Lusail Stadium",
                        "area": {"name": "Qatar"},
                    }
                ]
            },
        )
    )
    client = FootballDataClient(api_key="secret", base_url="https://api.football-data.org/v4")

    matches = client.get_competition_matches("WC")

    assert len(matches) == 1
    payload = matches[0]["match"]
    assert payload.external_id == "99"
    assert payload.home_team.name == "Argentina"
    assert payload.away_team.fifa_code == "FRA"
    assert payload.goals_home == 2
    assert payload.venue == "Lusail Stadium"


@respx.mock
def test_football_data_client_retries_on_rate_limit() -> None:
    sleeps: list[float] = []
    route = respx.get("https://api.football-data.org/v4/competitions").mock(
        side_effect=[
            Response(429, headers={"Retry-After": "0"}),
            Response(200, json={"competitions": [{"code": "WC"}]}),
        ]
    )
    client = FootballDataClient(
        api_key="secret",
        base_url="https://api.football-data.org/v4",
        sleeper=sleeps.append,
    )

    competitions = client.get_competitions()

    assert competitions == [{"code": "WC"}]
    assert route.call_count == 2
    assert sleeps == [0.0]


@respx.mock
def test_open_meteo_client_parses_weather_correctly() -> None:
    respx.get("https://archive-api.open-meteo.com/v1/archive").mock(
        return_value=Response(
            200,
            json={
                "hourly": {
                    "time": ["2026-06-12T20:00", "2026-06-12T21:00"],
                    "temperature_2m": [18.5, 17.1],
                    "relative_humidity_2m": [64, 66],
                    "wind_speed_10m": [12.2, 10.8],
                    "precipitation_probability": [25, 30],
                }
            },
        )
    )
    client = OpenMeteoClient(
        forecast_url="https://api.open-meteo.com/v1/forecast",
        historical_url="https://archive-api.open-meteo.com/v1/archive",
    )

    weather = client.fetch_weather_at(
        latitude=25.0,
        longitude=-80.0,
        match_datetime=datetime(2026, 6, 12, 20, 20, tzinfo=timezone.utc),
    )

    assert weather is not None
    assert weather.temperature == 18.5
    assert weather.humidity == 64.0
    assert weather.wind_speed == 12.2
    assert weather.rain_probability == 25.0


def test_world_football_elo_client_parses_headerless_tsv_and_maps_codes() -> None:
    from app.ingestion.elo_rating_client import WorldFootballEloClient

    client = WorldFootballEloClient(ratings_url="https://example.com/World.tsv")

    frame = client._parse_table("1\t1\tAR\t2115\n2\t2\tFR\t2063\n")

    assert frame.iloc[0]["team_code"] == "AR"
    assert float(frame.iloc[1]["rating_value"]) == 2063.0
