# import httpx
# import asyncio
# from app.config import settings
# from app.database import get_database
# from datetime import datetime, timedelta
# from typing import List

# class NewsFetcher:
#     def __init__(self):
#         self.api_key = settings.news_api_key
#         self.base_url = "https://newsapi.org/v2"
        
#     async def fetch_news(self, category: str = "general", language: str = "en") -> List[dict]:
#         """Fetch news - FIXED for real Hindi content"""
#         try:
#             if language == "hi":
#                 # For REAL Hindi news - use specific Hindi sources
#                 hindi_sources = "the-times-of-india"  # They have Hindi content
                
#                 # Use 'everything' endpoint for better Hindi results
#                 from datetime import datetime, timedelta
#                 yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
                
#                 url = f"{self.base_url}/everything?q=भारत OR india&language=hi&from={yesterday}&sortBy=publishedAt&apiKey={self.api_key}"
                
#                 if category != "general":
#                     # Add category keyword in Hindi and English
#                     category_map = {
#                         "technology": "technology OR प्रौद्योगिकी",
#                         "business": "business OR व्यापार",
#                         "sports": "sports OR खेल",
#                         "entertainment": "entertainment OR मनोरंजन",
#                         "health": "health OR स्वास्थ्य",
#                         "science": "science OR विज्ञान"
#                     }
#                     keyword = category_map.get(category, category)
#                     url = f"{self.base_url}/everything?q={keyword}&language=hi&from={yesterday}&sortBy=publishedAt&apiKey={self.api_key}"
#             else:
#                 # English news - standard approach
#                 url = f"{self.base_url}/top-headlines?category={category}&language={language}&apiKey={self.api_key}"
            
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(url, timeout=30.0)
                
#                 if response.status_code == 200:
#                     data = response.json()
#                     articles = data.get("articles", [])
#                     # Filter out articles with missing essential data
#                     filtered = [a for a in articles if a.get("title") and a.get("description")]
#                     print(f"✅ Fetched {len(filtered)} articles for {category}/{language}")
#                     return filtered
#                 else:
#                     print(f"❌ Error: {response.status_code} - {response.text}")
#                     return []
#         except Exception as e:
#             print(f"❌ Error in fetch_news: {e}")
#             return []
    
#     async def save_to_database(self, articles: List[dict], category: str, language: str):
#         """Save articles - FIXED to prevent empty cards"""
#         db = get_database()
#         collection = db["news"]
        
#         saved_count = 0
#         for article in articles:
#             try:
#                 # STRICT validation - no empty cards
#                 if not article.get("title") or not article.get("description"):
#                     continue
                
#                 # Check if already exists
#                 existing = await collection.find_one({"url": article.get("url")})
#                 if existing:
#                     continue
                
#                 news_doc = {
#                     "title": article.get("title"),
#                     "description": article.get("description") or "No description available",
#                     "content": article.get("content") or article.get("description"),
#                     "url": article.get("url"),
#                     "urlToImage": article.get("urlToImage"),
#                     "publishedAt": datetime.fromisoformat(
#                         article.get("publishedAt", datetime.utcnow().isoformat()).replace("Z", "+00:00")
#                     ),
#                     "source": {
#                         "id": article.get("source", {}).get("id"),
#                         "name": article.get("source", {}).get("name", "Unknown")
#                     },
#                     "language": language,
#                     "category": category,
#                     "aiSummary": None,
#                     "audioSummaryUrl": None,
#                     "createdAt": datetime.utcnow(),
#                     "updatedAt": datetime.utcnow()
#                 }
                
#                 await collection.insert_one(news_doc)
#                 saved_count += 1
                        
#             except Exception as e:
#                 print(f"Error saving article: {e}")
#                 continue
        
#         print(f"💾 Saved {saved_count} new articles for {category}/{language}")
#         return saved_count
    
#     async def fetch_and_store_all_categories(self):
#         """Optimized for free tier - Real Hindi + English"""
        
#         total_saved = 0
        
#         # English news (5 categories = 5 API calls)
#         print("📰 Fetching English news...")
#         en_categories = ["general", "technology", "business", "sports", "entertainment"]
        
#         for category in en_categories:
#             articles = await self.fetch_news(category, "en")
#             saved = await self.save_to_database(articles, category, "en")
#             total_saved += saved
#             await asyncio.sleep(2)
        
#         # REAL Hindi news (3 categories = 3 API calls)
#         print("📰 Fetching REAL Hindi news...")
#         hi_categories = ["general", "technology", "business"]
        
#         for category in hi_categories:
#             articles = await self.fetch_news(category, "hi")
#             saved = await self.save_to_database(articles, category, "hi")
#             total_saved += saved
#             await asyncio.sleep(2)
        
#         print(f"✅ Total: {total_saved} articles (8 API calls used)")
        
#         # ✅ CRITICAL: Send notification if new articles were saved
#         # if total_saved > 0:
#         #     try:
#         #         # Import here to avoid circular dependency
#         #         from firebase_admin import messaging
                
#         #         # Get all subscriber tokens
#         #         db = get_database()
#         #         collection = db["notification_tokens"]
#         #         cursor = collection.find({})
#         #         tokens = []
#         #         async for doc in cursor:
#         #             if doc.get("token"):
#         #                 tokens.append(doc["token"])
                
#         #         if tokens:
#         #             print(f"📬 Sending notification to {len(tokens)} subscribers...")
                    
#         #             # Create notification message
#         #             message = messaging.MulticastMessage(
#         #                 notification=messaging.Notification(
#         #                     title=f"📰 {total_saved} New Articles!",
#         #                     body="Fresh news just arrived. Check out the latest updates!"
#         #                 ),
#         #                 tokens=tokens
#         #             )
                    
#         #             # Send notification
#         #             response = messaging.send_multicast(message)
#         #             print(f"✅ Sent: {response.success_count} | Failed: {response.failure_count}")
                    
#         #             # Remove invalid tokens
#         #             if response.failure_count > 0:
#         #                 invalid_tokens = []
#         #                 for idx, resp in enumerate(response.responses):
#         #                     if not resp.success:
#         #                         invalid_tokens.append(tokens[idx])
                        
#         #                 if invalid_tokens:
#         #                     await collection.delete_many({"token": {"$in": invalid_tokens}})
#         #                     print(f"🗑️ Removed {len(invalid_tokens)} invalid tokens")
#         #         else:
#         #             print("⚠️ No subscribers found - skipping notification")
                    
#         #     except Exception as e:
#         #         print(f"⚠️ Notification error: {e}")
        
#         # return total_saved
#         # ✅ CRITICAL: Send notification if new articles were saved
#         if total_saved > 0:
#             try:
#                 # Import here to avoid circular dependency
#                 from firebase_admin import messaging
                
#                 # Get all subscriber tokens
#                 db = get_database()
#                 collection = db["notification_tokens"]
#                 cursor = collection.find({})
#                 tokens = []
#                 async for doc in cursor:
#                     if doc.get("token"):
#                         tokens.append(doc["token"])
                
#                 if tokens:
#                     print(f"📬 Sending notification to {len(tokens)} subscribers...")
                    
#                     # Send to each token individually (compatible with all versions)
#                     success_count = 0
#                     failure_count = 0
#                     invalid_tokens = []
                    
#                     for idx, token in enumerate(tokens):
#                         try:
#                             message = messaging.Message(
#                                 notification=messaging.Notification(
#                                     title=f"📰 {total_saved} New Articles!",
#                                     body="Fresh news just arrived. Check out the latest updates!"
#                                 ),
#                                 token=token
#                             )
#                             messaging.send(message)
#                             success_count += 1
#                         except Exception as e:
#                             failure_count += 1
#                             invalid_tokens.append(token)
#                             print(f"❌ Failed to send to token {idx+1}: {e}")
                    
#                     print(f"✅ Sent: {success_count} | Failed: {failure_count}")
                    
#                     # Remove invalid tokens
#                     if invalid_tokens:
#                         await collection.delete_many({"token": {"$in": invalid_tokens}})
#                         print(f"🗑️ Removed {len(invalid_tokens)} invalid tokens")
#                 else:
#                     print("⚠️ No subscribers found - skipping notification")
                    
#             except Exception as e:
#                 print(f"⚠️ Notification error: {e}")
#                 import traceback
#                 traceback.print_exc()
        
#         return total_saved
    
#     async def cleanup_old_articles(self):
#         """Delete articles older than 7 days"""
#         db = get_database()
#         collection = db["news"]
        
#         seven_days_ago = datetime.utcnow() - timedelta(days=7)
#         result = await collection.delete_many({"createdAt": {"$lt": seven_days_ago}})
        
#         print(f"🗑️ Deleted {result.deleted_count} old articles")
#         return result.deleted_count

# news_fetcher = NewsFetcher()


import httpx
import asyncio
from app.config import settings
from app.database import get_database
from datetime import datetime, timedelta
from typing import List

class NewsFetcher:
    def __init__(self):
        self.api_key = settings.news_api_key
        self.base_url = "https://newsapi.org/v2"
        
    async def fetch_news(self, category: str = "general", language: str = "en") -> List[dict]:
        """Fetch news - FIXED for real Hindi content"""
        try:
            if language == "hi":
                # For REAL Hindi news - use specific Hindi sources
                hindi_sources = "the-times-of-india"  # They have Hindi content
                
                # Use 'everything' endpoint for better Hindi results
                from datetime import datetime, timedelta
                yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                url = f"{self.base_url}/everything?q=भारत OR india&language=hi&from={yesterday}&sortBy=publishedAt&apiKey={self.api_key}"
                
                if category != "general":
                    # Add category keyword in Hindi and English
                    category_map = {
                        "technology": "technology OR प्रौद्योगिकी",
                        "business": "business OR व्यापार",
                        "sports": "sports OR खेल",
                        "entertainment": "entertainment OR मनोरंजन",
                        "health": "health OR स्वास्थ्य",
                        "science": "science OR विज्ञान"
                    }
                    keyword = category_map.get(category, category)
                    url = f"{self.base_url}/everything?q={keyword}&language=hi&from={yesterday}&sortBy=publishedAt&apiKey={self.api_key}"
            else:
                # English news - standard approach
                url = f"{self.base_url}/top-headlines?category={category}&language={language}&apiKey={self.api_key}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    # Filter out articles with missing essential data
                    filtered = [a for a in articles if a.get("title") and a.get("description")]
                    print(f"✅ Fetched {len(filtered)} articles for {category}/{language}")
                    return filtered
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            print(f"❌ Error in fetch_news: {e}")
            return []
    
    async def save_to_database(self, articles: List[dict], category: str, language: str):
        """Save articles - FIXED to prevent empty cards"""
        db = get_database()
        collection = db["news"]
        
        saved_count = 0
        for article in articles:
            try:
                # STRICT validation - no empty cards
                if not article.get("title") or not article.get("description"):
                    continue
                
                # Check if already exists
                existing = await collection.find_one({"url": article.get("url")})
                if existing:
                    continue
                
                news_doc = {
                    "title": article.get("title"),
                    "description": article.get("description") or "No description available",
                    "content": article.get("content") or article.get("description"),
                    "url": article.get("url"),
                    "urlToImage": article.get("urlToImage"),
                    "publishedAt": datetime.fromisoformat(
                        article.get("publishedAt", datetime.utcnow().isoformat()).replace("Z", "+00:00")
                    ),
                    "source": {
                        "id": article.get("source", {}).get("id"),
                        "name": article.get("source", {}).get("name", "Unknown")
                    },
                    "language": language,
                    "category": category,
                    "aiSummary": None,
                    "audioSummaryUrl": None,
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
                
                await collection.insert_one(news_doc)
                saved_count += 1
                        
            except Exception as e:
                print(f"Error saving article: {e}")
                continue
        
        print(f"💾 Saved {saved_count} new articles for {category}/{language}")
        return saved_count
    
    async def fetch_and_store_all_categories(self):
        """Optimized for free tier - Real Hindi + English"""
        
        total_saved = 0
        
        # English news - ALL 7 categories (7 API calls)
        print("📰 Fetching English news...")
        en_categories = ["general", "technology", "business", "sports", "entertainment", "health", "science"]
        
        for category in en_categories:
            articles = await self.fetch_news(category, "en")
            saved = await self.save_to_database(articles, category, "en")
            total_saved += saved
            await asyncio.sleep(2)
        
        # Hindi news - ALL 7 categories (7 API calls)
        print("📰 Fetching REAL Hindi news...")
        hi_categories = ["general", "technology", "business", "sports", "entertainment", "health", "science"]
        
        for category in hi_categories:
            articles = await self.fetch_news(category, "hi")
            saved = await self.save_to_database(articles, category, "hi")
            total_saved += saved
            await asyncio.sleep(2)
        
        print(f"✅ Total: {total_saved} articles (14 API calls used)")
        
        # ✅ CRITICAL: Send notification if new articles were saved
        if total_saved > 0:
            try:
                # Import here to avoid circular dependency
                from firebase_admin import messaging
                
                # Get all subscriber tokens
                db = get_database()
                collection = db["notification_tokens"]
                cursor = collection.find({})
                tokens = []
                async for doc in cursor:
                    if doc.get("token"):
                        tokens.append(doc["token"])
                
                if tokens:
                    print(f"📬 Sending notification to {len(tokens)} subscribers...")
                    
                    # Send to each token individually (compatible with all versions)
                    success_count = 0
                    failure_count = 0
                    invalid_tokens = []
                    
                    for idx, token in enumerate(tokens):
                        try:
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title=f"📰 {total_saved} New Articles!",
                                    body="Fresh news just arrived. Check out the latest updates!"
                                ),
                                token=token
                            )
                            messaging.send(message)
                            success_count += 1
                        except Exception as e:
                            failure_count += 1
                            invalid_tokens.append(token)
                            print(f"❌ Failed to send to token {idx+1}: {e}")
                    
                    print(f"✅ Sent: {success_count} | Failed: {failure_count}")
                    
                    # Remove invalid tokens
                    if invalid_tokens:
                        await collection.delete_many({"token": {"$in": invalid_tokens}})
                        print(f"🗑️ Removed {len(invalid_tokens)} invalid tokens")
                else:
                    print("⚠️ No subscribers found - skipping notification")
                    
            except Exception as e:
                print(f"⚠️ Notification error: {e}")
                import traceback
                traceback.print_exc()
        
        return total_saved
    
    async def cleanup_old_articles(self):
        """Delete articles older than 7 days"""
        db = get_database()
        collection = db["news"]
        
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        result = await collection.delete_many({"createdAt": {"$lt": seven_days_ago}})
        
        print(f"🗑️ Deleted {result.deleted_count} old articles")
        return result.deleted_count

news_fetcher = NewsFetcher()