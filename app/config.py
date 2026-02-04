from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str
    database_name: str = "news_platform"
    
    # News API
    news_api_key: str
    
    # AI API (optional - use one)
    huggingface_api_key: str = ""
    gemini_api_key: str = ""
    
    # Firebase
    firebase_credentials_path: str
    
    # CORS
    allowed_origins: str = "http://localhost:5173"
    
    # Environment
    environment: str = "development"
    
    # Admin API Key
    admin_api_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

settings = Settings()