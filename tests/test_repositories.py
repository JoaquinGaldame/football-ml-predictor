from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.database.models import Match, Team
from app.database.repositories import MatchPayload, MatchRepository, TeamPayload, TeamStatsPayload, WeatherPayload


def test_match_repository_upserts_without_duplicates(session) -> None:
    repository = MatchRepository(session)
    payload = MatchPayload(
        external_id="ext-1",
        date=datetime(2024, 1, 1, 20, 0),
        competition="Friendly",
        home_team=TeamPayload(name="Argentina", country="Argentina", fifa_code="ARG"),
        away_team=TeamPayload(name="Brazil", country="Brazil", fifa_code="BRA"),
        goals_home=1,
        goals_away=0,
        neutral_site=False,
        venue="Monumental",
        country="Argentina",
    )
    match = repository.upsert_match(payload)
    repository.upsert_team_stats(
        match,
        [
            TeamStatsPayload(team_name="Argentina", shots=10, shots_on_target=5),
            TeamStatsPayload(team_name="Brazil", shots=7, shots_on_target=3),
        ],
    )
    repository.upsert_weather(match, WeatherPayload(temperature=23.0))

    payload.goals_home = 2
    repository.upsert_match(payload)

    assert session.query(Team).count() == 2
    assert session.query(Match).count() == 1
    assert session.scalar(select(Match).where(Match.external_id == "ext-1")).goals_home == 2
