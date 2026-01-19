from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_DB: str = "powerplex"
    POSTGRES_USER: str = "powerplex"
    POSTGRES_PASSWORD: str = "powerplex"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"

settings = Settings()
