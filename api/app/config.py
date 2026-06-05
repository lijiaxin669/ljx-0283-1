from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/swim_registration"
    REDIS_URL: str = "redis://redis:6379/0"
    ORDER_EXPIRE_MINUTES: int = 15
    PAYMENT_NOTIFY_URL: str = ""
    ADMIN_SECRET: str = "changeme"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
