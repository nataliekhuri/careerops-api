"""Helpers for running Alembic migrations inside a given connection (used by tests)."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def alembic_config(connection: Connection) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.attributes["connection"] = connection
    config.attributes["configure_logger"] = False  # keep pytest's logging setup
    return config


def upgrade(connection: Connection, revision: str = "head") -> None:
    command.upgrade(alembic_config(connection), revision)


def downgrade(connection: Connection, revision: str = "base") -> None:
    command.downgrade(alembic_config(connection), revision)
