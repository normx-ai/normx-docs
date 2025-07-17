from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os

class Settings(BaseSettings):
    """
    Configuration de l'application avec variables d'environnement
    Les valeurs par défaut sont vides pour forcer l'utilisation du .env
    """
    
    # Environment
    ENV: str = Field(default="production", env="ENV")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["Accept", "Content-Type", "Authorization"],
        env="CORS_ALLOW_HEADERS"
    )
    
    # Allowed hosts
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_TRACK_STARTED: bool = Field(default=True, env="CELERY_TASK_TRACK_STARTED")
    CELERY_TASK_TIME_LIMIT: int = Field(default=30 * 60, env="CELERY_TASK_TIME_LIMIT")
    CELERY_BEAT_SCHEDULE_FILENAME: str = Field(default="celerybeat-schedule", env="CELERY_BEAT_SCHEDULE_FILENAME")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(default="", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(default="", env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field(default="NormX Docs", env="SMTP_FROM_NAME")
    
    # SMS (Africa's Talking)
    SMS_ENABLED: bool = Field(default=False, env="SMS_ENABLED")
    AFRICASTALKING_USERNAME: str = Field(default="", env="AFRICASTALKING_USERNAME")
    AFRICASTALKING_API_KEY: str = Field(default="", env="AFRICASTALKING_API_KEY")
    AFRICASTALKING_SENDER_ID: str = Field(default="", env="AFRICASTALKING_SENDER_ID")
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # Upload
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, env="MAX_UPLOAD_SIZE_MB")
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"],
        env="ALLOWED_UPLOAD_EXTENSIONS"
    )
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    LOG_MAX_SIZE_MB: int = Field(default=10, env="LOG_MAX_SIZE_MB")
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_DEFAULT: str = Field(default="100/hour", env="RATE_LIMIT_DEFAULT")
    RATE_LIMIT_STORAGE_URL: str = Field(default="redis://localhost:6379/3", env="RATE_LIMIT_STORAGE_URL")
    
    # Session
    SESSION_SECRET_KEY: Optional[str] = Field(default=None, env="SESSION_SECRET_KEY")
    SESSION_COOKIE_NAME: str = Field(default="normx_session", env="SESSION_COOKIE_NAME")
    SESSION_COOKIE_MAX_AGE: int = Field(default=86400, env="SESSION_COOKIE_MAX_AGE")
    SESSION_COOKIE_SECURE: bool = Field(default=True, env="SESSION_COOKIE_SECURE")
    SESSION_COOKIE_HTTPONLY: bool = Field(default=True, env="SESSION_COOKIE_HTTPONLY")
    SESSION_COOKIE_SAMESITE: str = Field(default="lax", env="SESSION_COOKIE_SAMESITE")
    
    # Frontend URL
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    # API Settings
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    PROJECT_NAME: str = Field(default="NormX Docs", env="PROJECT_NAME")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @validator("CORS_ORIGINS", "ALLOWED_HOSTS", "ALLOWED_UPLOAD_EXTENSIONS", pre=True)
    def parse_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v
    
    @validator("SESSION_SECRET_KEY", pre=True)
    def set_session_secret(cls, v, values):
        if not v and "SECRET_KEY" in values:
            return values["SECRET_KEY"]
        return v

# Créer une instance unique des settings
settings = Settings()
