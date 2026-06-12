from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("fifa_code", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_teams_name", "teams", ["name"], unique=True)
    op.create_index("ix_teams_fifa_code", "teams", ["fifa_code"], unique=False)

    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_venues_name", "venues", ["name"], unique=False)

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("competition", sa.String(length=255), nullable=True),
        sa.Column("team_home_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("team_away_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("goals_home", sa.Integer(), nullable=True),
        sa.Column("goals_away", sa.Integer(), nullable=True),
        sa.Column("neutral_site", sa.Boolean(), nullable=False),
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=True),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("external_id", name="uq_matches_external_id"),
    )
    op.create_index("ix_matches_external_id", "matches", ["external_id"], unique=False)
    op.create_index("ix_matches_date", "matches", ["date"], unique=False)
    op.create_index("ix_matches_team_home_id", "matches", ["team_home_id"], unique=False)
    op.create_index("ix_matches_team_away_id", "matches", ["team_away_id"], unique=False)
    op.create_index("ix_matches_venue_id", "matches", ["venue_id"], unique=False)

    op.create_table(
        "team_match_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("shots", sa.Integer(), nullable=True),
        sa.Column("shots_on_target", sa.Integer(), nullable=True),
        sa.Column("possession", sa.Float(), nullable=True),
        sa.Column("xg", sa.Float(), nullable=True),
        sa.Column("corners", sa.Integer(), nullable=True),
        sa.Column("fouls", sa.Integer(), nullable=True),
        sa.UniqueConstraint("match_id", "team_id", name="uq_team_match_stats_match_team"),
    )
    op.create_index("ix_team_match_stats_match_id", "team_match_stats", ["match_id"], unique=False)
    op.create_index("ix_team_match_stats_team_id", "team_match_stats", ["team_id"], unique=False)

    op.create_table(
        "player_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("player_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("reported_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_player_status_team_id", "player_status", ["team_id"], unique=False)

    op.create_table(
        "weather_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("humidity", sa.Float(), nullable=True),
        sa.Column("wind_speed", sa.Float(), nullable=True),
        sa.Column("rain_probability", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_weather_snapshots_match_id", "weather_snapshots", ["match_id"], unique=False)

    op.create_table(
        "team_ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("rating_type", sa.String(length=64), nullable=False),
        sa.Column("rating_value", sa.Float(), nullable=False),
        sa.Column("rating_date", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("team_id", "rating_type", "rating_date", name="uq_team_rating_key"),
    )
    op.create_index("ix_team_ratings_team_id", "team_ratings", ["team_id"], unique=False)
    op.create_index("ix_team_ratings_rating_date", "team_ratings", ["rating_date"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id"), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("predicted_home_win", sa.Float(), nullable=False),
        sa.Column("predicted_draw", sa.Float(), nullable=False),
        sa.Column("predicted_away_win", sa.Float(), nullable=False),
        sa.Column("predicted_result", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_predictions_match_id", "predictions", ["match_id"], unique=False)

    op.create_table(
        "training_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("trained_at", sa.DateTime(), nullable=False),
        sa.Column("dataset_size", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("log_loss", sa.Float(), nullable=False),
        sa.Column("f1_score", sa.Float(), nullable=False),
        sa.Column("notes", sa.String(length=1024), nullable=True),
    )
    op.create_index("ix_training_runs_model_version", "training_runs", ["model_version"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("algorithm", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_model_versions_version", "model_versions", ["version"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_model_versions_version", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index("ix_training_runs_model_version", table_name="training_runs")
    op.drop_table("training_runs")
    op.drop_index("ix_predictions_match_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_team_ratings_rating_date", table_name="team_ratings")
    op.drop_index("ix_team_ratings_team_id", table_name="team_ratings")
    op.drop_table("team_ratings")
    op.drop_index("ix_weather_snapshots_match_id", table_name="weather_snapshots")
    op.drop_table("weather_snapshots")
    op.drop_index("ix_player_status_team_id", table_name="player_status")
    op.drop_table("player_status")
    op.drop_index("ix_team_match_stats_team_id", table_name="team_match_stats")
    op.drop_index("ix_team_match_stats_match_id", table_name="team_match_stats")
    op.drop_table("team_match_stats")
    op.drop_index("ix_matches_team_away_id", table_name="matches")
    op.drop_index("ix_matches_team_home_id", table_name="matches")
    op.drop_index("ix_matches_venue_id", table_name="matches")
    op.drop_index("ix_matches_date", table_name="matches")
    op.drop_index("ix_matches_external_id", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_venues_name", table_name="venues")
    op.drop_table("venues")
    op.drop_index("ix_teams_fifa_code", table_name="teams")
    op.drop_index("ix_teams_name", table_name="teams")
    op.drop_table("teams")
