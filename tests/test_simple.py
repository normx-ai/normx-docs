"""
Test simple pour vérifier que l'environnement de test fonctionne
"""
import os

# Configuration minimale pour les tests
os.environ["ENV"] = "test"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/15"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/15"
os.environ["UPLOAD_ALLOWED_EXTENSIONS"] = ".pdf,.doc,.docx"
os.environ["UPLOAD_MAX_SIZE_MB"] = "10"
os.environ["UPLOAD_DIRECTORY"] = "/tmp/test_uploads"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["LOG_FILE_PATH"] = "/tmp/test_logs"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["TWO_FACTOR_ISSUER"] = "Test App"
os.environ["ALLOWED_HOSTS"] = "localhost"
os.environ["DEBUG"] = "true"


def test_environment_setup():
    """Test que l'environnement est correctement configuré"""
    assert os.environ.get("ENV") == "test"
    assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"
    

def test_import_config():
    """Test que la configuration peut être importée"""
    from app.core.config import settings
    assert settings.ENV == "test"
    assert settings.SECRET_KEY.get_secret_value() == "test-secret-key-32-chars-minimum"
    

def test_password_security():
    """Test basique de sécurité des mots de passe"""
    from app.core.security import get_password_hash, verify_password
    
    password = "TestPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)