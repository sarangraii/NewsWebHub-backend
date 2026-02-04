from fastapi import APIRouter, HTTPException, Header
from app.database import get_database
from bson import ObjectId
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotificationRequest(BaseModel):
    article_id: str
    type: str  # "breaking" or "topic"
    topic: str = None  # Required if type is "topic"

class SubscribeRequest(BaseModel):
    token: str

# ===== TOKEN-BASED ENDPOINTS (for your frontend) =====

@router.post("/subscribe")
async def subscribe_to_notifications(request: SubscribeRequest):
    """Subscribe to push notifications using FCM token"""
    try:
        db = get_database()
        collection = db["notification_tokens"]
        
        # Check if token already exists
        existing = await collection.find_one({"token": request.token})
        
        if existing:
            # Update timestamp
            await collection.update_one(
                {"token": request.token},
                {"$set": {"updatedAt": datetime.utcnow()}}
            )
            print(f"✅ Updated token subscription")
            return {"message": "Token updated", "subscribed": True}
        else:
            # Insert new token
            await collection.insert_one({
                "token": request.token,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            })
            print(f"✅ New subscriber added")
            return {"message": "Subscribed successfully", "subscribed": True}
    
    except Exception as e:
        print(f"❌ Subscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unsubscribe")
async def unsubscribe_from_notifications(request: SubscribeRequest):
    """Unsubscribe from push notifications"""
    try:
        db = get_database()
        collection = db["notification_tokens"]
        
        result = await collection.delete_one({"token": request.token})
        
        if result.deleted_count > 0:
            print(f"✅ Subscriber removed")
            return {"message": "Unsubscribed successfully"}
        else:
            return {"message": "Token not found"}
    
    except Exception as e:
        print(f"❌ Unsubscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscribers")
async def get_subscriber_count():
    """Get total number of subscribers - Public endpoint for stats"""
    try:
        db = get_database()
        collection = db["notification_tokens"]
        
        count = await collection.count_documents({})
        
        return {"subscribers": count}
    
    except Exception as e:
        print(f"❌ Error getting subscriber count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_notification(x_api_key: str = Header(None)):
    """
    Send a test notification to all subscribers
    
    ⚠️ PRODUCTION: Requires API key in header: X-API-Key
    For local development, works without key
    """
    # ✅ PRODUCTION SECURITY: Check API key
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        admin_api_key = os.getenv("ADMIN_API_KEY")
        if not admin_api_key or x_api_key != admin_api_key:
            raise HTTPException(
                status_code=403, 
                detail="Forbidden: Valid API key required for test notifications in production"
            )
    
    try:
        db = get_database()
        collection = db["notification_tokens"]
        
        # Get all tokens
        cursor = collection.find({})
        tokens = []
        async for doc in cursor:
            if doc.get("token"):
                tokens.append(doc["token"])
        
        if not tokens:
            return {"message": "No subscribers found", "success": 0, "failure": 0}
        
        print(f"📬 Sending test notification to {len(tokens)} subscribers...")
        
        # Send notification using Firebase
        from firebase_admin import messaging
        
        # Send to each token individually
        success_count = 0
        failure_count = 0
        invalid_tokens = []
        
        for idx, token in enumerate(tokens):
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Test Notification 🔔",
                        body="This is a test from NewsHub! Your notifications are working perfectly."
                    ),
                    token=token
                )
                messaging.send(message)
                success_count += 1
            except Exception as e:
                failure_count += 1
                invalid_tokens.append(token)
                print(f"❌ Failed to send to token {idx+1}: {e}")
        
        print(f"✅ Total - Sent: {success_count} | Failed: {failure_count}")
        
        # Remove invalid tokens
        if invalid_tokens:
            await collection.delete_many({"token": {"$in": invalid_tokens}})
            print(f"🗑️ Removed {len(invalid_tokens)} invalid tokens")
        
        return {
            "success": success_count,
            "failure": failure_count,
            "total_subscribers": len(tokens),
            "environment": environment
        }
        
    except Exception as e:
        print(f"❌ Test notification error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ===== TOPIC-BASED ENDPOINTS =====

@router.post("/send")
async def send_notification(request: NotificationRequest, x_api_key: str = Header(None)):
    """
    Send notification for an article
    
    ⚠️ PRODUCTION: Requires API key
    """
    # Check API key in production
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        admin_api_key = os.getenv("ADMIN_API_KEY")
        if not admin_api_key or x_api_key != admin_api_key:
            raise HTTPException(status_code=403, detail="Forbidden: Valid API key required")
    
    db = get_database()
    collection = db["news"]
    
    try:
        from app.services.notification_service import notification_service
        
        # Get article
        article = await collection.find_one({"_id": ObjectId(request.article_id)})
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Send notification based on type
        if request.type == "breaking":
            response = await notification_service.send_breaking_news(article)
        elif request.type == "topic" and request.topic:
            response = await notification_service.send_topic_notification(article, request.topic)
        else:
            raise HTTPException(status_code=400, detail="Invalid notification type")
        
        return {
            "success": True,
            "message": "Notification sent",
            "response": response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics")
async def get_available_topics():
    """Get list of available notification topics - Public endpoint"""
    return {
        "topics": [
            {"id": "breaking_news", "name": "Breaking News", "icon": "🚨"},
            {"id": "technology", "name": "Technology", "icon": "💻"},
            {"id": "business", "name": "Business", "icon": "💼"},
            {"id": "sports", "name": "Sports", "icon": "⚽"},
            {"id": "entertainment", "name": "Entertainment", "icon": "🎬"},
            {"id": "health", "name": "Health", "icon": "🏥"},
            {"id": "science", "name": "Science", "icon": "🔬"},
        ]
    }