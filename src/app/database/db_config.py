import os
from pydantic_settings import BaseSettings
from pydantic_settings import BaseSettings, SettingsConfigDict

# Encontrar la raíz del proyecto (donde está el .env)
# Desde db_config.py -> database -> app -> src -> raíz


class Settings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    secret_key: str
    app_env: str = "production"


  # === CONFIGURACIÓN DEL LLM ===
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 500
    llm_timeout: int = 30


   
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a PostgreSQL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"





    class Config:
        # En producción, las variables vienen del sistema
        env_file = ".env" if os.path.exists(".env") else None
        env_file_encoding = "utf-8"
        case_sensitive = False



settings = Settings()

