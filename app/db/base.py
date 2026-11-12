from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Predictable constraint and index names, so migrations can refer to them reliably.
# (Primary keys keep PostgreSQL's default "<table>_pkey" name used by existing tables.)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all database tables."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
