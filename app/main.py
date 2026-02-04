from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import news, notifications
from app.utils.scheduler import start_scheduler, stop_scheduler
from app.services.news_fetcher import news_fetcher
from pathlib import Path
import os

# # ✅ CRITICAL: Initialize Firebase FIRST, before anything else
# try:
#     import firebase_admin
#     from firebase_admin import credentials
    
#     cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
#     if os.path.exists(cred_path):
#         cred = credentials.Certificate(cred_path)
#         firebase_admin.initialize_app(cred)
#         print("✅ Firebase initialized for notifications")
#     else:
#         print("⚠️ Firebase credentials not found - notifications disabled")
# except Exception as e:
#     print(f"⚠️ Firebase initialization failed: {e}")



# ✅ CRITICAL: Initialize Firebase FIRST, before anything else
try:
    import firebase_admin
    from firebase_admin import credentials
    import json
    import os

    firebase_json = os.getenv("FIREBASE_CREDENTIALS")  # <- Secret from Render

    if firebase_json:
        cred = credentials.Certificate(json.loads(firebase_json))
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized for notifications")
    else:
        print("⚠️ Firebase credentials not found - notifications disabled")
except Exception as e:
    print(f"⚠️ Firebase initialization failed: {e}")







@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    start_scheduler()
    
    # Create static directory
    Path("static/audio").mkdir(parents=True, exist_ok=True)
    
    print("Fetching initial news...")
    await news_fetcher.fetch_and_store_all_categories()
    
    yield
    
    # Shutdown
    stop_scheduler()
    await close_mongo_connection()

app = FastAPI(
    title="News Aggregation Platform API",
    description="API for news aggregation with AI summaries",
    version="2.0.0",
    lifespan=lifespan
)

# ✅ FIXED: CORS middleware with correct port
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:5173",  # ✅ Correct Vite frontend port
#         "http://localhost:5174",  # Backup port
#         "http://127.0.0.1:5173",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # Docker frontend
        "http://localhost",       # Docker
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(news.router)
app.include_router(notifications.router)

@app.get("/")
async def root():
    return {
        "message": "News Aggregation Platform API",
        "version": "2.0.0",
        "features": ["Hindi Support", "AI Summaries", "Voice Reading", "Push Notifications"],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}