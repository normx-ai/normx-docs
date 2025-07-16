from typing import Optional
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    ENV: str = "production"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql://normx_docs_user:Normx2025Docs!@localhost:5432/normx_docs_db"
    SECRET_KEY: str = "2UdqQyYrcZM5PHaghFMSxm7jtmZlQZRXZt0Q9yN5cGk"
    JWT_SECRET: str = "7D5ghjnxP3mX8PbLBXJ54rrcooolp34Booz-FwKJqGk"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: list = ["https://docs.normx-ai.com", "http://localhost:3000"]
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = ["Accept", "Content-Type", "Authorization"]
    ALLOWED_HOSTS: list = ["docs.normx-ai.com", "localhost", "127.0.0.1"]
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Email config
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "noreply@normx-ai.com"
    SMTP_PASSWORD: str = "password"
    SMTP_FROM_EMAIL: str = "noreply@normx-ai.com"
    SMTP_FROM_NAME: str = "NormX Docs"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    EMAIL_TEMPLATES_DIR: str = "./templates/emails"
    
    # Upload config
    UPLOAD_MAX_SIZE_MB: int = 10
    UPLOAD_ALLOWED_EXTENSIONS: list = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"]
    UPLOAD_PATH: str = "./uploads"
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    LOG_MAX_SIZE_MB: int = 100
    LOG_BACKUP_COUNT: int = 10
    
    # API
    API_TIMEOUT: int = 30
    SENTRY_DSN: Optional[str] = None
    
    # Database config
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    def get_secret_key(self): 
        return self.SECRET_KEY
    
    def get_smtp_password(self): 
        return self.SMTP_PASSWORD
    
    class Config:
        env_file = None

settings = Settings()
