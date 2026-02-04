import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

async def add_hindi():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client["news_platform"]
    
    # Get some English articles and duplicate as Hindi
    articles = await db.news.find({"language": "en"}).limit(20).to_list(20)
    
    for art in articles:
        art.pop("_id")
        art["language"] = "hi"
        art["category"] = art.get("category", "general")
        await db.news.insert_one(art)
    
    print("✅ Added 20 Hindi articles!")
    client.close()

asyncio.run(add_hindi())