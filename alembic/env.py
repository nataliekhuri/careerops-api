"""
Alembic migration environment.

The database URL comes from the app's settings (DATABASE_URL or DB_* values in
.env or environment variables), so no credentials are stored in alembic.ini.

Tests can pass an existing connection via `config.attributes["connection"]`
to run migrations inside a throwaway schema.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool, text

from alembic import context
from app import models  # noqa: F401  (registers tables with Base.metadata)
from app.core.config import get_settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL without connecting ('alembic upgrade head --sql')."""
    context.configure(
        url=get_settings().database_url.render_as_string(hide_password=True),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the database."""
    connection = config.attributes.get("connection")
    if connection is not None:
        _run(connection)
        return

    engine = create_engine(get_settings().database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        _run(connection)
    engine.dispose()


# Arbitrary constant key for a PostgreSQL advisory lock that serialises migration runs.
MIGRATION_LOCK_KEY = 7_240_317_001


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        # If several app instances start at once (e.g. RUN_MIGRATIONS=true on a
        # deploy), only one runs migrations at a time; the others wait, then find
        # nothing left to do. The lock is released automatically at commit/rollback.
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": MIGRATION_LOCK_KEY})
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
