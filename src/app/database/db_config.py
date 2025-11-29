import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    db_host: str
    db_port: Optional[int] = 5432
    db_name: str
    db_user: str
    db_password: str
    secret_key: str
    app_env: str = "production"

    @field_validator('db_port', mode='before')
    @classmethod
    def validate_port(cls, v):
        """Convierte cadenas vacías a None y usa el valor por defecto"""
        if v == '' or v is None:
            return 5432
        return int(v)

    class Config:
        env_file = ".env" if os.path.exists(".env") else None
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()