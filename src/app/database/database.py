# src/app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .db_config import settings

# Construir URL con SSL para Neon
DATABASE_URL = (
    f"postgresql://{settings.db_user}:{settings.db_password}@"
    f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# Añadir SSL si estamos en producción
if settings.app_env == "production":
    DATABASE_URL += "?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Desactivar logs en producción
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()