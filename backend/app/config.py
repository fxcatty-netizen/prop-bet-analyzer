from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # App
    APP_NAME: str = "PropBet Analyzer"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    
    # BallDontLie API
    BALLDONTLIE_API_KEY: str
    BALLDONTLIE_BASE_URL: str = "https://api.balldontlie.io"
    
    # Anthropic API for OCR
    ANTHROPIC_API_KEY: str = ""  # Optional, for image upload feature
    
    # Server
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Rate Limiting
    API_RATE_LIMIT_PER_MINUTE: int = 30
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
