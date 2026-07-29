from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from app.database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    field = Column(String, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    why_matters = Column(Text, nullable=False)
    source_name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)  # URL immagine articolo
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    is_trending = Column(Boolean, default=False)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    briefing_id = Column(Integer, nullable=False)
    liked = Column(Boolean, nullable=True)
    created_at = Column(DateTime, server_default=func.now())