from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Source(BaseModel):
    id: Optional[str] = None
    name: str

class NewsArticle(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    urlToImage: Optional[str] = None
    publishedAt: datetime
    source: Source
    language: str = "en"  # 'en' or 'hi'
    category: str = "general"
    aiSummary: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class NewsResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    urlToImage: Optional[str] = None
    publishedAt: datetime
    source: Source
    language: str
    category: str
    aiSummary: Optional[str] = None
    createdAt: datetime