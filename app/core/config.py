from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url
from sqlalchemy.exc import ArgumentError

POSTGRES_SCHEMES = {"postgres", "postgresql", "postgresql+psycopg"}


class Settings(BaseSettings):
    """App settings, read from environment variables or the .env file.

    The database can be configured either with separate DB_* values (local
    development) or with a single DATABASE_URL (as provided by hosting platforms
    such as Render). DATABASE_URL takes priority when both are set.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    database_url_value: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "database_url_value"),
        description="Full PostgreSQL connection URL",
    )

    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "careerops"
    db_user: str = "careerops_user"
    db_password: SecretStr | None = None
    # Seconds to wait for a database connection before failing. Without a limit,
    # requests can hang for minutes when the database is unreachable.
    db_connect_timeout: int = Field(default=5, ge=1, le=60)

    # Authentication. The secret signs login tokens: keep it private, at least 32
    # characters, and different in every environment. The API refuses to start
    # without it (database migrations do not need it).
    jwt_secret_key: SecretStr | None = None
    access_token_expire_minutes: int = Field(default=60, ge=5, le=60 * 24)

    # Browser origins allowed to call the API (comma-separated), e.g. the frontend URL.
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("jwt_secret_key")
    @classmethod
    def secret_must_be_long(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and len(value.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return value

    @field_validator("database_url_value")
    @classmethod
    def must_be_postgres_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return value
        try:
            scheme = make_url(value.get_secret_value()).drivername
        except ArgumentError:
            raise ValueError("DATABASE_URL is not a valid database URL") from None
        if scheme not in POSTGRES_SCHEMES:
            raise ValueError(f"DATABASE_URL must be a PostgreSQL URL, not {scheme!r}")
        return value

    @model_validator(mode="after")
    def require_credentials(self) -> "Settings":
        if self.database_url_value is None and self.db_password is None:
            raise ValueError("Set DATABASE_URL or DB_PASSWORD to configure the database")
        return self

    @property
    def database_url(self) -> URL:
        if self.database_url_value is not None:
            url = make_url(self.database_url_value.get_secret_value()).set(drivername="postgresql+psycopg")
            if "connect_timeout" not in url.query:
                url = url.update_query_dict({"connect_timeout": str(self.db_connect_timeout)})
            return url

        # URL.create escapes special characters in the password safely.
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value() if self.db_password else None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"connect_timeout": str(self.db_connect_timeout)},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
