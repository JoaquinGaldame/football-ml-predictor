from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.db import Base


@pytest.fixture(autouse=True)
def test_settings_isolation(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("ENABLE_REAL_INGESTION", "false")
    monkeypatch.setenv("ENABLE_PLAYER_STATUS", "false")
    monkeypatch.delenv("FOOTBALL_DATA_API_KEY", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = session_local()
    try:
        yield db
        db.commit()
    finally:
        db.close()
