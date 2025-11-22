# src/app/database/db_config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    secret_key: str
    app_env: str = "development"  # valor por defecto opcional

    class Config:
        env_file = "../.env"   # indica el archivo donde están las variables
        env_file_encoding = "utf-8"

# Instancia global que se usará en toda la app
settings = Settings()
