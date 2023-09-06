from pydantic_settings import BaseSettings


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


settings = Settings()
