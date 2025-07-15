"""
Script de débogage de la configuration
"""
import os
import sys

# Configuration minimale
os.environ["ENV"] = "test"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'  # Format JSON
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/15"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/15"
os.environ["UPLOAD_ALLOWED_EXTENSIONS"] = '".pdf,.doc,.docx"'
os.environ["UPLOAD_MAX_SIZE_MB"] = "10"
os.environ["UPLOAD_DIRECTORY"] = "/tmp/test_uploads"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["LOG_FILE_PATH"] = "/tmp/test_logs"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["TWO_FACTOR_ISSUER"] = "Test App"
os.environ["ALLOWED_HOSTS"] = "localhost"
os.environ["DEBUG"] = "true"

try:
    from app.core.config import settings
    print("✅ Configuration chargée avec succès!")
    print(f"ENV: {settings.ENV}")
    print(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()