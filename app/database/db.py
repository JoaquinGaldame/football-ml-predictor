from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings


Base = declarative_base()
settings = get_settings()

engine = create_engine(
    settings.database_url,
    future=True,
    echo=False,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_additive_schema_updates()


def _apply_additive_schema_updates() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        tables = set(inspector.get_table_names())
        if "venues" not in tables:
            connection.execute(
                text(
                    """
                    CREATE TABLE venues (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        city VARCHAR(255),
                        country VARCHAR(255),
                        latitude FLOAT,
                        longitude FLOAT,
                        source VARCHAR(255),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_venues_name ON venues (name)"))

        if "matches" in tables:
            match_columns = {column["name"] for column in inspector.get_columns("matches")}
            if "venue_id" not in match_columns:
                connection.execute(text("ALTER TABLE matches ADD COLUMN venue_id INTEGER"))
                connection.execute(text("CREATE INDEX IF NOT EXISTS ix_matches_venue_id ON matches (venue_id)"))


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
