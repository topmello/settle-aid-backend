from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict


class Settings(BaseSettings):
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PORT: str
    DATABASE_PASSWORD: str
    DATABASE_USERNAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MAPBOX_ACCESS_TOKEN: str
    DOC_USERNAME: str
    DOC_PASSWORD: str
    REFRESH_SECRET_KEY: str
    REFRESH_TOKEN_EXPIRE_DAYS: int
    REDIS_HOSTNAME: str
    REDIS_PORT: str
    REDIS_PASSWORD: str
    USER_CACHE_EXPIRY: int

    model_config: ConfigDict = {
        "env_file": ".env",
        "extra": "ignore",
        "env_file_encoding": "utf-8"
    }


settings = Settings()
