from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://crucible:crucible_dev@localhost:5555/crucible"
    test_database_url: str = (
        "postgresql+asyncpg://crucible:crucible_dev@localhost:5555/crucible_test"
    )
    redis_url: str = "redis://localhost:6380/0"


settings = Settings()
