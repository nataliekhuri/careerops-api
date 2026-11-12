from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """App settings, read from environment variables or the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5433
    db_name: str = "careerops"
    db_user: str = "careerops_user"
    db_password: SecretStr
    # Seconds to wait for a database connection before failing. Without a limit,
    # requests can hang for minutes when the database is unreachable.
    db_connect_timeout: int = Field(default=5, ge=1, le=60)

    @property
    def database_url(self) -> URL:
        # URL.create escapes special characters in the password safely.
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"connect_timeout": str(self.db_connect_timeout)},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
