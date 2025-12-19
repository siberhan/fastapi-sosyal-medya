from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    # --- YENİ EKLENENLER ---
    refresh_token_expire_days: int = 7
    redis_hostname: str = "localhost" # Docker'da çalışırken "redis" olacak
    redis_port: int = 6379
    # -----------------------

    class Config:
        env_file = ".env"

settings = Settings()