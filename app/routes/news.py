from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.database import get_database
from app.models.news import NewsResponse
from app.services.ai_summarizer import ai_summarizer
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/api/news", tags=["news"])

def serialize_news(news_doc) -> dict:
    """FIXED - Better serialization"""
    return {
        "id": str(news_doc["_id"]),
        "title": news_doc.get("title", "No title"),
        "description": news_doc.get("description", "No description available"),
        "content": news_doc.get("content", news_doc.get("description", "")),
        "url": news_doc.get("url", ""),
        "urlToImage": news_doc.get("urlToImage"),
        "publishedAt": news_doc.get("publishedAt", datetime.utcnow()),
        "source": news_doc.get("source", {"name": "Unknown", "id": None}),
        "language": news_doc.get("language", "en"),
        "category": news_doc.get("category", "general"),
        "aiSummary": news_doc.get("aiSummary"),
        "audioSummaryUrl": news_doc.get("audioSummaryUrl"),
        "createdAt": news_doc.get("createdAt", datetime.utcnow())
    }

@router.get("/", response_model=dict)
async def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None
):
    """Get news with filters"""
    db = get_database()
    collection = db["news"]
    
    query = {}
    
    # STRICT language filter
    if language:
        query["language"] = language
    
    if category and category != "":
        query["category"] = category
    
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Also filter out articles with missing data
    query["title"] = {"$exists": True, "$ne": ""}
    query["description"] = {"$exists": True, "$ne": ""}
    
    total = await collection.count_documents(query)
    skip = (page - 1) * limit
    # cursor = collection.find(query).sort("publishedAt", -1).skip(skip).limit(limit)
    cursor = collection.find(query).sort([
    ("publishedAt", -1),
    ("createdAt", -1)
]).skip(skip).limit(limit)
    articles = []
    async for doc in cursor:
        articles.append(serialize_news(doc))
    
    return {
        "articles": articles,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }

@router.get("/trending", response_model=List[NewsResponse])
async def get_trending_news(limit: int = Query(10, ge=1, le=50)):
    """Get trending news"""
    db = get_database()
    collection = db["news"]
    
    # Filter out incomplete articles
    query = {
        "title": {"$exists": True, "$ne": ""},
        "description": {"$exists": True, "$ne": ""}
    }
    
    cursor = collection.find(query).sort("publishedAt", -1).limit(limit)
    
    articles = []
    async for doc in cursor:
        articles.append(serialize_news(doc))
    
    return articles

@router.get("/{article_id}", response_model=NewsResponse)
async def get_article(article_id: str):
    """Get single article"""
    db = get_database()
    collection = db["news"]
    
    try:
        doc = await collection.find_one({"_id": ObjectId(article_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Article not found")
        return serialize_news(doc)
    except:
        raise HTTPException(status_code=400, detail="Invalid article ID")

@router.post("/{article_id}/summarize")
async def generate_article_summary(article_id: str):
    """Generate comprehensive AI summary - FIXED"""
    db = get_database()
    collection = db["news"]
    
    try:
        doc = await collection.find_one({"_id": ObjectId(article_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Article not found")
        
        if doc.get("aiSummary") and len(doc.get("aiSummary", "")) > 100:
            return {
                "summary": doc["aiSummary"],
                "audioUrl": doc.get("audioSummaryUrl"),
                "cached": True
            }
        
        title = doc.get("title", "")
        description = doc.get("description", "")
        content = doc.get("content", "")
        url = doc.get("url", "")
        language = doc.get("language", "en")
        
        print(f"Generating summary for: {title[:50]}...")
        
        summary = await ai_summarizer.generate_summary(
            title=title,
            description=description,
            content=content,
            url=url,
            language=language
        )
        
        print(f"Summary generated: {len(summary)} chars")
        
        audio_url = ai_summarizer.generate_audio_summary(summary, language)
        
        await collection.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"aiSummary": summary, "audioSummaryUrl": audio_url, "updatedAt": datetime.utcnow()}}
        )
        
        return {"summary": summary, "audioUrl": audio_url, "cached": False}
    except Exception as e:
        print(f"Summary error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))