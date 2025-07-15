"""
Configuration sécurisée pour la production
Remplace config.py avec des variables d'environnement obligatoires
"""
import os
from typing import List, Optional, Union, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, SecretStr
import secrets


class Settings(BaseSettings):
    """Configuration avec validation stricte pour la production"""
    
    # Environment
    ENV: str = Field(
        default="production",
        env="ENV",
        description="Environment (development, staging, production)"
    )
    DEBUG: bool = Field(
        default=False,
        env="DEBUG",
        description="Debug mode - MUST be False in production"
    )
    
    # Base de données - OBLIGATOIRE
    DATABASE_URL: str = Field(
        ...,  # Pas de valeur par défaut = obligatoire
        env="DATABASE_URL",
        description="PostgreSQL connection URL"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=20,
        env="DATABASE_POOL_SIZE",
        ge=5,
        le=100
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=40,
        env="DATABASE_MAX_OVERFLOW",
        ge=0,
        le=200
    )
    
    # JWT et Sécurité - OBLIGATOIRE
    SECRET_KEY: SecretStr = Field(
        ...,  # Pas de valeur par défaut = obligatoire
        env="SECRET_KEY",
        min_length=32,
        description="Secret key for JWT - Use: openssl rand -hex 32"
    )
    ALGORITHM: str = Field(
        default="HS256",
        env="ALGORITHM"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24 heures
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=30,
        le=10080  # Max 1 semaine
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30,
        env="REFRESH_TOKEN_EXPIRE_DAYS",
        ge=7,
        le=90
    )
    
    # Redis - OBLIGATOIRE
    REDIS_URL: str = Field(
        ...,  # Pas de valeur par défaut = obligatoire
        env="REDIS_URL",
        description="Redis connection URL"
    )
    
    # Celery
    CELERY_BROKER_URL: str = Field(
        ...,
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        ...,
        env="CELERY_RESULT_BACKEND"
    )
    
    # CORS - Configuration stricte
    CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed origins"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_ALLOW_METHODS"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["Accept", "Content-Type", "Authorization"],
        env="CORS_ALLOW_HEADERS"
    )
    
    # Hosts autorisés - OBLIGATOIRE en production
    ALLOWED_HOSTS: List[str] = Field(
        default_factory=list,
        env="ALLOWED_HOSTS",
        description="Comma-separated list of allowed hosts"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    LOG_FILE: str = Field(
        default="./logs/app.log",
        env="LOG_FILE"
    )
    LOG_MAX_SIZE_MB: int = Field(
        default=100,
        env="LOG_MAX_SIZE_MB",
        ge=10,
        le=1000
    )
    LOG_BACKUP_COUNT: int = Field(
        default=10,
        env="LOG_BACKUP_COUNT",
        ge=1,
        le=100
    )
    
    # Email - Configuration requise pour les notifications
    SMTP_HOST: str = Field(
        ...,
        env="SMTP_HOST"
    )
    SMTP_PORT: int = Field(
        ...,
        env="SMTP_PORT",
        ge=1,
        le=65535
    )
    SMTP_USER: str = Field(
        ...,
        env="SMTP_USER"
    )
    SMTP_PASSWORD: SecretStr = Field(
        ...,
        env="SMTP_PASSWORD"
    )
    SMTP_FROM_EMAIL: str = Field(
        ...,
        env="SMTP_FROM_EMAIL"
    )
    SMTP_FROM_NAME: str = Field(
        default="NormX Docs",
        env="SMTP_FROM_NAME"
    )
    SMTP_TLS: bool = Field(
        default=True,
        env="SMTP_TLS"
    )
    SMTP_SSL: bool = Field(
        default=False,
        env="SMTP_SSL"
    )
    
    # Sécurité des uploads
    UPLOAD_MAX_SIZE_MB: int = Field(
        default=10,
        env="UPLOAD_MAX_SIZE_MB",
        ge=1,
        le=100
    )
    UPLOAD_ALLOWED_EXTENSIONS: List[str] = Field(
        default=[
            ".pdf", ".doc", ".docx", ".xls", ".xlsx",
            ".png", ".jpg", ".jpeg", ".gif"
        ],
        env="UPLOAD_ALLOWED_EXTENSIONS"
    )
    UPLOAD_PATH: str = Field(
        default="./uploads",
        env="UPLOAD_PATH"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        env="RATE_LIMIT_PER_MINUTE",
        ge=10,
        le=1000
    )
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        env="RATE_LIMIT_PER_HOUR",
        ge=100,
        le=10000
    )
    
    # Monitoring (optionnel)
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        env="SENTRY_DSN"
    )
    
    # API externe
    API_TIMEOUT: int = Field(
        default=30,
        env="API_TIMEOUT",
        ge=5,
        le=300
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Forcer la lecture depuis l'environnement en production
        env_ignore_empty=False,
        extra="forbid"  # Rejeter les champs non définis
    )
    
    @field_validator('ENV')
    def validate_env(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return v
    
    @field_validator('DEBUG')
    def validate_debug_in_production(cls, v, info):
        if info.data.get('ENV') == 'production' and v is True:
            raise ValueError("DEBUG must be False in production")
        return v
    
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v: SecretStr):
        if len(v.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if v.get_secret_value() == "dev-secret-key-change-this-in-production":
            raise ValueError("Default SECRET_KEY detected. Please generate a secure key.")
        return v
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            # Si c'est une chaîne, la diviser par virgules
            return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    @field_validator('ALLOWED_HOSTS')
    def validate_allowed_hosts_in_production(cls, v, info):
        if info.data.get('ENV') == 'production' and not v:
            raise ValueError("ALLOWED_HOSTS must be set in production")
        return v
    
    @field_validator('CORS_ORIGINS', mode='before')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Si c'est une chaîne, la diviser par virgules
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('UPLOAD_ALLOWED_EXTENSIONS', mode='before')
    def parse_upload_extensions(cls, v):
        if isinstance(v, str):
            # Si c'est une chaîne, la diviser par virgules
            return [ext.strip() for ext in v.split(',') if ext.strip()]
        return v
    
    
    @field_validator('DATABASE_URL')
    def validate_database_url(cls, v):
        # En développement, autoriser localhost
        import os
        if os.getenv("ENV") == "development":
            return v
        # En production, vérifier que ce n'est pas l'URL par défaut
        if "gd_ia_2025" in str(v) or "localhost:5432" in str(v):
            raise ValueError("Default DATABASE_URL detected. Please use a secure connection string.")
        return v
    
    def get_smtp_password(self) -> str:
        """Retourne le mot de passe SMTP déchiffré"""
        return self.SMTP_PASSWORD.get_secret_value()
    
    def get_secret_key(self) -> str:
        """Retourne la clé secrète déchiffrée"""
        return self.SECRET_KEY.get_secret_value()


# Instance unique de configuration
try:
    # En développement, utiliser le fichier .env.development
    import os
    env_file = None
    if os.getenv("ENV_FILE"):
        env_file = os.getenv("ENV_FILE")
    elif os.getenv("ENV", "development") == "development" and os.path.exists(".env.development"):
        env_file = ".env.development"
    elif os.getenv("ENV") == "test" and os.path.exists(".env.test"):
        env_file = ".env.test"
    
    if env_file:
        settings = Settings(_env_file=env_file)
    else:
        settings = Settings()
except Exception as e:
    # En cas d'erreur de configuration, afficher un message clair
    import sys
    print(f"ERREUR DE CONFIGURATION: {e}", file=sys.stderr)
    print("\nAssurez-vous que toutes les variables d'environnement requises sont définies.", file=sys.stderr)
    print("Consultez .env.production.example pour la liste complète.", file=sys.stderr)
    sys.exit(1)