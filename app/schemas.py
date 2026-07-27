from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


# --- Input ---

class BriefingCreate(BaseModel):
    field: str
    title: str
    url: HttpUrl
    summary: str
    why_matters: str
    source_name: str
    published_at: Optional[datetime] = None
    is_trending: bool = False


class FeedbackCreate(BaseModel):
    briefing_id: int
    liked: bool


# --- Output ---

class BriefingOut(BaseModel):
    id: int
    field: str
    title: str
    url: str
    summary: str
    why_matters: str
    source_name: str
    published_at: Optional[datetime]
    created_at: datetime
    is_trending: bool

    class Config:
        from_attributes = True  # compatibile con SQLAlchemy ORM


class FeedbackOut(BaseModel):
    id: int
    briefing_id: int
    liked: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True