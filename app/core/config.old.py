import os
from typing import List, Optional, Union, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field


class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    
    # Base de données
    DATABASE_URL: str = "postgresql://gd_user:gd_ia_2025@localhost:5432/gd_ia_comptable"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # JWT et Sécurité
    SECRET_KEY: str = "dev-secret-key-change-this-in-production-very-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # ML et IA
    MODEL_PATH: str = "./models/"
    MODEL_VERSION: str = "v1"
    
    # API
    API_KEY: Optional[str] = None
    API_TIMEOUT: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"]
    )
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM_EMAIL: str = Field(default="noreply@cabinet-comptable.fr")
    SMTP_FROM_NAME: str = Field(default="Cabinet Comptable")
    SMTP_TLS: bool = Field(default=True)
    SMTP_SSL: bool = Field(default=False)
    
    # Email templates
    EMAIL_TEMPLATES_DIR: str = Field(default="./templates/emails")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()