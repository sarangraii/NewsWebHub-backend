import firebase_admin
from firebase_admin import credentials, messaging
from app.config import settings
from pathlib import Path
import os

class NotificationService:
    def __init__(self):
        self.initialized = False
        self.setup_firebase()
    
    def setup_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            cred_path = Path(os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json"))
            
            if not cred_path.exists():
                print("⚠️ Firebase credentials not found - notifications disabled")
                return
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(cred_path))
                firebase_admin.initialize_app(cred)
                self.initialized = True
                print("✅ Firebase initialized for notifications")
            else:
                self.initialized = True
        except Exception as e:
            print(f"❌ Firebase setup error: {e}")
    
    async def send_breaking_news(self, article: dict):
        """Send breaking news notification to all users"""
        if not self.initialized:
            return
        
        try:
            title = article.get("title", "Breaking News")[:100]
            body = article.get("description", "")[:200]
            article_id = str(article.get("_id", ""))
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"🚨 Breaking: {title}",
                    body=body,
                ),
                data={
                    "articleId": article_id,
                    "type": "breaking",
                    "url": f"/article/{article_id}"
                },
                topic="breaking_news"  # All users subscribed to this topic
            )
            
            response = messaging.send(message)
            print(f"✅ Breaking news sent: {response}")
            return response
            
        except Exception as e:
            print(f"❌ Notification error: {e}")
            return None
    
    async def send_topic_notification(self, article: dict, topic: str):
        """Send notification for specific topic (Sports, Tech, etc.)"""
        if not self.initialized:
            return
        
        try:
            title = article.get("title", "")[:100]
            body = article.get("description", "")[:200]
            article_id = str(article.get("_id", ""))
            
            # Topic names must match Firebase format: letters, numbers, and underscores only
            safe_topic = topic.lower().replace(" ", "_").replace("-", "_")
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"{topic}: {title}",
                    body=body,
                ),
                data={
                    "articleId": article_id,
                    "type": "topic",
                    "topic": topic,
                    "url": f"/article/{article_id}"
                },
                topic=safe_topic
            )
            
            response = messaging.send(message)
            print(f"✅ Topic notification sent ({topic}): {response}")
            return response
            
        except Exception as e:
            print(f"❌ Topic notification error: {e}")
            return None

notification_service = NotificationService()