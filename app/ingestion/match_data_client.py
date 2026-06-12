from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone

from app.config import Settings, get_settings
from app.database.repositories import MatchPayload, TeamPayload, TeamStatsPayload, VenuePayload
from app.ingestion.football_data_client import FootballDataClient


class MatchDataClient(ABC):
    def fetch_competitions(self) -> list[dict]:
        return []

    def fetch_teams(self) -> list[TeamPayload]:
        return []

    def fetch_historical_matches(self) -> list[dict]:
        return []

    def fetch_upcoming_matches(self) -> list[dict]:
        return []

    def fetch_matches(self) -> list[dict]:
        return [*self.fetch_historical_matches(), *self.fetch_upcoming_matches()]


class MockMatchDataClient(MatchDataClient):
    def fetch_historical_matches(self) -> list[dict]:
        raw_matches: list[dict] = [
            {
                "match": MatchPayload(
                    external_id="mock-20240110-arg-bra",
                    date=datetime(2024, 1, 10, 20, 0),
                    competition="Friendly",
                    home_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    away_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
                    goals_home=2,
                    goals_away=1,
                    neutral_site=False,
                    venue="Monumental",
                    country="Argentina",
                    venue_data=VenuePayload(
                        name="Monumental",
                        city="Buenos Aires",
                        country="Argentina",
                        latitude=-34.5453,
                        longitude=-58.4497,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Argentina", shots=12, shots_on_target=6, possession=58.0, xg=1.7, corners=5, fouls=11),
                    TeamStatsPayload(team_name="Brazil", shots=10, shots_on_target=4, possession=42.0, xg=1.2, corners=3, fouls=14),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240215-fra-esp",
                    date=datetime(2024, 2, 15, 21, 0),
                    competition="Friendly",
                    home_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    away_team=TeamPayload(name="Spain", country="Spain", fifa_code="ESP"),
                    goals_home=1,
                    goals_away=1,
                    neutral_site=False,
                    venue="Stade de France",
                    country="France",
                    venue_data=VenuePayload(
                        name="Stade de France",
                        city="Saint-Denis",
                        country="France",
                        latitude=48.9244,
                        longitude=2.3601,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="France", shots=11, shots_on_target=5, possession=52.0, xg=1.5, corners=4, fouls=10),
                    TeamStatsPayload(team_name="Spain", shots=13, shots_on_target=5, possession=48.0, xg=1.3, corners=6, fouls=9),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240320-bra-fra",
                    date=datetime(2024, 3, 20, 20, 45),
                    competition="Friendly",
                    home_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
                    away_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    goals_home=0,
                    goals_away=2,
                    neutral_site=True,
                    venue="MetLife Stadium",
                    country="United States",
                    venue_data=VenuePayload(
                        name="MetLife Stadium",
                        city="East Rutherford",
                        country="United States",
                        latitude=40.8135,
                        longitude=-74.0745,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Brazil", shots=8, shots_on_target=2, possession=49.0, xg=0.8, corners=2, fouls=13),
                    TeamStatsPayload(team_name="France", shots=14, shots_on_target=7, possession=51.0, xg=1.9, corners=5, fouls=8),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240418-esp-arg",
                    date=datetime(2024, 4, 18, 19, 30),
                    competition="Friendly",
                    home_team=TeamPayload(name="Spain", country="Spain", fifa_code="ESP"),
                    away_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    goals_home=0,
                    goals_away=1,
                    neutral_site=False,
                    venue="Santiago Bernabeu",
                    country="Spain",
                    venue_data=VenuePayload(
                        name="Santiago Bernabeu",
                        city="Madrid",
                        country="Spain",
                        latitude=40.4531,
                        longitude=-3.6883,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Spain", shots=9, shots_on_target=3, possession=55.0, xg=1.0, corners=7, fouls=7),
                    TeamStatsPayload(team_name="Argentina", shots=8, shots_on_target=4, possession=45.0, xg=1.4, corners=3, fouls=12),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240522-fra-arg",
                    date=datetime(2024, 5, 22, 20, 0),
                    competition="Friendly",
                    home_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    away_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    goals_home=1,
                    goals_away=2,
                    neutral_site=True,
                    venue="Wembley",
                    country="England",
                    venue_data=VenuePayload(
                        name="Wembley",
                        city="London",
                        country="England",
                        latitude=51.556,
                        longitude=-0.2796,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="France", shots=15, shots_on_target=6, possession=50.0, xg=1.6, corners=5, fouls=11),
                    TeamStatsPayload(team_name="Argentina", shots=12, shots_on_target=6, possession=50.0, xg=1.8, corners=4, fouls=10),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240628-bra-esp",
                    date=datetime(2024, 6, 28, 18, 0),
                    competition="Copa Demo",
                    home_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
                    away_team=TeamPayload(name="Spain", country="Spain", fifa_code="ESP"),
                    goals_home=3,
                    goals_away=2,
                    neutral_site=False,
                    venue="Maracana",
                    country="Brazil",
                    venue_data=VenuePayload(
                        name="Maracana",
                        city="Rio de Janeiro",
                        country="Brazil",
                        latitude=-22.9121,
                        longitude=-43.2302,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Brazil", shots=16, shots_on_target=8, possession=53.0, xg=2.1, corners=6, fouls=15),
                    TeamStatsPayload(team_name="Spain", shots=12, shots_on_target=6, possession=47.0, xg=1.5, corners=4, fouls=11),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240716-arg-fra",
                    date=datetime(2024, 7, 16, 21, 0),
                    competition="Copa Demo",
                    home_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    away_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    goals_home=1,
                    goals_away=0,
                    neutral_site=True,
                    venue="Hard Rock Stadium",
                    country="United States",
                    venue_data=VenuePayload(
                        name="Hard Rock Stadium",
                        city="Miami Gardens",
                        country="United States",
                        latitude=25.958,
                        longitude=-80.2389,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Argentina", shots=10, shots_on_target=4, possession=46.0, xg=1.1, corners=5, fouls=9),
                    TeamStatsPayload(team_name="France", shots=13, shots_on_target=4, possession=54.0, xg=1.0, corners=7, fouls=8),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240812-esp-bra",
                    date=datetime(2024, 8, 12, 20, 0),
                    competition="Nations Demo",
                    home_team=TeamPayload(name="Spain", country="Spain", fifa_code="ESP"),
                    away_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
                    goals_home=2,
                    goals_away=0,
                    neutral_site=False,
                    venue="Mestalla",
                    country="Spain",
                    venue_data=VenuePayload(
                        name="Mestalla",
                        city="Valencia",
                        country="Spain",
                        latitude=39.4747,
                        longitude=-0.3581,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Spain", shots=14, shots_on_target=7, possession=57.0, xg=1.9, corners=8, fouls=10),
                    TeamStatsPayload(team_name="Brazil", shots=7, shots_on_target=2, possession=43.0, xg=0.7, corners=2, fouls=14),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20240909-fra-bra",
                    date=datetime(2024, 9, 9, 20, 0),
                    competition="Nations Demo",
                    home_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    away_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
                    goals_home=2,
                    goals_away=2,
                    neutral_site=False,
                    venue="Lyon Stadium",
                    country="France",
                    venue_data=VenuePayload(
                        name="Lyon Stadium",
                        city="Lyon",
                        country="France",
                        latitude=45.7651,
                        longitude=4.982,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="France", shots=13, shots_on_target=6, possession=51.0, xg=1.7, corners=5, fouls=12),
                    TeamStatsPayload(team_name="Brazil", shots=12, shots_on_target=5, possession=49.0, xg=1.6, corners=6, fouls=13),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20241011-arg-esp",
                    date=datetime(2024, 10, 11, 21, 15),
                    competition="Nations Demo",
                    home_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    away_team=TeamPayload(name="Spain", country="Spain", fifa_code="ESP"),
                    goals_home=3,
                    goals_away=1,
                    neutral_site=False,
                    venue="Cordoba",
                    country="Argentina",
                    venue_data=VenuePayload(
                        name="Cordoba",
                        city="Cordoba",
                        country="Argentina",
                        latitude=-31.4135,
                        longitude=-64.181,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Argentina", shots=17, shots_on_target=9, possession=54.0, xg=2.3, corners=7, fouls=9),
                    TeamStatsPayload(team_name="Spain", shots=10, shots_on_target=4, possession=46.0, xg=1.1, corners=3, fouls=12),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20241114-bra-arg",
                    date=datetime(2024, 11, 14, 20, 30),
                    competition="Qualifier Demo",
                    home_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
                    away_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
                    goals_home=1,
                    goals_away=1,
                    neutral_site=False,
                    venue="Mineirao",
                    country="Brazil",
                    venue_data=VenuePayload(
                        name="Mineirao",
                        city="Belo Horizonte",
                        country="Brazil",
                        latitude=-19.8658,
                        longitude=-43.971,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="Brazil", shots=11, shots_on_target=4, possession=52.0, xg=1.2, corners=5, fouls=15),
                    TeamStatsPayload(team_name="Argentina", shots=10, shots_on_target=4, possession=48.0, xg=1.1, corners=4, fouls=13),
                ],
            },
            {
                "match": MatchPayload(
                    external_id="mock-20241201-fra-esp",
                    date=datetime(2024, 12, 1, 19, 45),
                    competition="Qualifier Demo",
                    home_team=TeamPayload(name="France", country="France", fifa_code="FRA"),
                    away_team=TeamPayload(name="Spain", country="Spain", fifa_code="ESP"),
                    goals_home=0,
                    goals_away=1,
                    neutral_site=False,
                    venue="Marseille",
                    country="France",
                    venue_data=VenuePayload(
                        name="Marseille",
                        city="Marseille",
                        country="France",
                        latitude=43.2698,
                        longitude=5.3959,
                        source="mock_seed",
                    ),
                ),
                "stats": [
                    TeamStatsPayload(team_name="France", shots=9, shots_on_target=3, possession=47.0, xg=0.9, corners=4, fouls=11),
                    TeamStatsPayload(team_name="Spain", shots=12, shots_on_target=5, possession=53.0, xg=1.4, corners=5, fouls=9),
                ],
            },
        ]
        return raw_matches

    def fetch_teams(self) -> list[TeamPayload]:
        teams: dict[str, TeamPayload] = {}
        for item in self.fetch_historical_matches():
            match: MatchPayload = item["match"]
            teams[match.home_team.name] = match.home_team
            teams[match.away_team.name] = match.away_team
        return list(teams.values())


class FootballDataMatchDataClient(MatchDataClient):
    def __init__(self, football_data_client: FootballDataClient, settings: Settings | None = None) -> None:
        self.football_data_client = football_data_client
        self.settings = settings or get_settings()
        self._competition_cache: dict[str, list[dict]] = {}

    def fetch_competitions(self) -> list[dict]:
        return self.football_data_client.get_competitions()

    def fetch_historical_matches(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [item for item in self._fetch_all_competition_matches() if item["match"].date <= now]

    def fetch_upcoming_matches(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [item for item in self._fetch_all_competition_matches() if item["match"].date > now]

    def fetch_teams(self) -> list[TeamPayload]:
        teams: dict[str, TeamPayload] = {}
        for item in self._fetch_all_competition_matches():
            match: MatchPayload = item["match"]
            teams[match.home_team.name] = match.home_team
            teams[match.away_team.name] = match.away_team
        return list(teams.values())

    def _fetch_all_competition_matches(self) -> list[dict]:
        matches: list[dict] = []
        for code in self.settings.competition_codes:
            if code not in self._competition_cache:
                try:
                    self._competition_cache[code] = self.football_data_client.get_competition_matches(code)
                except RuntimeError:
                    self._competition_cache[code] = []
                    continue
            matches.extend(self._competition_cache[code])
        deduplicated: dict[str, dict] = {}
        for item in matches:
            deduplicated[item["match"].external_id] = item
        return list(deduplicated.values())
