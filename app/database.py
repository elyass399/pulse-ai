from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite per sviluppo (async con aiosqlite per produzione)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # necessario per SQLite
)

# Sessione per le query
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base per i modelli
Base = declarative_base()


def get_db():
    """Dependency per FastAPI — apre e chiude sessione automaticamente."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()