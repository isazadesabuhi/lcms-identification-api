from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./lcms.db"
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "http://127.0.0.1:3000,"
        "http://127.0.0.1:3001"
    )

    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = True

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
