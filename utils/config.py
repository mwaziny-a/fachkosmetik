from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str = ""
    app_env: str = "development"
    max_upload_size_mb: int = 10
    allowed_image_types: list = ["image/jpeg", "image/png", "image/webp"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()