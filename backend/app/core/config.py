"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./tradequest.db"
    DATABASE_HOST: Optional[str] = None
    DATABASE_PORT: Optional[int] = None
    DATABASE_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    JWT_SECRET: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: Optional[str] = None
    
    # AWS Secrets Manager
    SECRETS_MANAGER_SECRET_NAME: Optional[str] = None
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # External APIs
    KRAKEN_API_URL: str = "https://api.kraken.com"
    COINBASE_API_URL: str = "https://api.exchange.coinbase.com"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    USE_S3_STORAGE: bool = False  # Set to True in production

    # AI/ML
    OPENAI_API_KEY: Optional[str] = None

    # Market Data APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    POLYGON_S3_ACCESS_KEY: Optional[str] = None
    POLYGON_S3_SECRET_KEY: Optional[str] = None
    
    # Email Service
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "verification@tradequest.tech"
    FROM_NAME: str = "TradeQuest"
    
    # SMS Service (Twilio)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Production Settings
    LOG_LEVEL: str = "INFO"
    WORKERS: int = 1
    
    def get_database_url(self) -> str:
        """Build database URL from components or use direct URL"""
        if self.DATABASE_URL and not self.DATABASE_URL.startswith("sqlite"):
            return self.DATABASE_URL
        
        if self.DATABASE_HOST:
            # Build PostgreSQL URL from components
            auth = ""
            if self.DATABASE_USER and self.DATABASE_PASSWORD:
                auth = f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@"
            elif self.DATABASE_USER:
                auth = f"{self.DATABASE_USER}@"
            
            port = f":{self.DATABASE_PORT}" if self.DATABASE_PORT else ""
            return f"postgresql://{auth}{self.DATABASE_HOST}{port}/{self.DATABASE_NAME or 'tradequest'}"
        
        return self.DATABASE_URL
    
    def get_redis_url(self) -> str:
        """Build Redis URL from components or use direct URL"""
        if self.REDIS_URL and not self.REDIS_URL.startswith("redis://localhost"):
            return self.REDIS_URL
        
        if self.REDIS_HOST:
            auth = ""
            if self.REDIS_PASSWORD:
                auth = f":{self.REDIS_PASSWORD}@"
            
            port = f":{self.REDIS_PORT}" if self.REDIS_PORT else ":6379"
            return f"redis://{auth}{self.REDIS_HOST}{port}"
        
        return self.REDIS_URL
    
    class Config:
        # Look for .env in the backend directory
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        case_sensitive = True
        extra = "allow"

# Global settings instance
settings = Settings()
