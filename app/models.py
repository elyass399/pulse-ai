from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    field = Column(String, nullable=False)  # tech, finance, sport, health, geo
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    summary = Column(Text, nullable=False)       # riassunto LLM
    why_matters = Column(Text, nullable=False)   # "Perché importa" LLM
    source_name = Column(String, nullable=False)  # es. "TechCrunch"
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_trending = Column(Boolean, default=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    briefing_id = Column(Integer, nullable=False)
    liked = Column(Boolean, nullable=True)  # True=👍, False=👎, None=non votato
    created_at = Column(DateTime, server_default=func.now())