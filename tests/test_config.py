"""Database settings: separate DB_* values or a single DATABASE_URL (as provided by Render)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make(**values) -> Settings:
    return Settings(_env_file=None, **values)


def test_separate_db_settings_build_the_url():
    url = make(db_host="db.local", db_port=5432, db_name="app", db_user="me", db_password="p@ss#1").database_url

    assert (url.drivername, url.host, url.port, url.database, url.username) == (
        "postgresql+psycopg",
        "db.local",
        5432,
        "app",
        "me",
    )
    assert url.password == "p@ss#1"
    assert url.query["connect_timeout"] == "5"


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_database_url_is_used_with_the_psycopg_driver(scheme):
    url = make(database_url_value=f"{scheme}://render_user:s3cr%40t@dpg-abc123-a/careerops_db").database_url

    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.database, url.username, url.password) == (
        "dpg-abc123-a",
        "careerops_db",
        "render_user",
        "s3cr@t",
    )
    assert url.query["connect_timeout"] == "5"


def test_database_url_takes_priority_over_separate_settings():
    settings = make(database_url_value="postgresql://u:p@remote-host/remote_db", db_host="localhost", db_password="x")

    assert settings.database_url.host == "remote-host"


def test_database_url_keeps_its_own_query_options():
    url = make(database_url_value="postgresql://u:p@h/db?sslmode=require&connect_timeout=9").database_url

    assert url.query["sslmode"] == "require"
    assert url.query["connect_timeout"] == "9"


def test_database_url_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@env-host/env_db")

    assert make().database_url.host == "env-host"


def test_database_url_is_not_shown_in_repr():
    settings = make(database_url_value="postgresql://u:topsecret@h/db")

    assert "topsecret" not in repr(settings)


@pytest.mark.parametrize("bad", ["mysql://u:p@h/db", "not a url"])
def test_non_postgres_database_url_is_rejected(bad):
    with pytest.raises(ValidationError):
        make(database_url_value=bad)


def test_a_password_or_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(ValidationError, match="DATABASE_URL or DB_PASSWORD"):
        make()
