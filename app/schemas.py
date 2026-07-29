from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class BriefingCreate(BaseModel):
    field: str
    title: str
    url: HttpUrl
    summary: str
    why_matters: str
    source_name: str
    image_url: Optional[str] = None  # NUOVO
    published_at: Optional[datetime] = None
    is_trending: bool = False


class BriefingOut(BaseModel):
    id: int
    field: str
    title: str
    url: str
    summary: str
    why_matters: str
    source_name: str
    image_url: Optional[str] = None  # NUOVO
    published_at: Optional[datetime]
    created_at: datetime
    is_trending: bool

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    briefing_id: int
    liked: bool


class FeedbackOut(BaseModel):
    id: int
    briefing_id: int
    liked: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True