from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/auth_db"

    JWT_SECRET_KEY: str = "change-me-to-a-real-secret-key-min-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    APP_ENV: str = "development"
    DEBUG: bool = True


settings = Settings()
