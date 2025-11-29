import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_port: Optional[int] = 5432
    db_name: str
    db_user: str
    db_password: str
    secret_key: str
    app_env: str = "production"

    class Config:
        # En producción, las variables vienen del sistema
        env_file = ".env" if os.path.exists(".env") else None
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
