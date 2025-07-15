"""
Configuration pytest et fixtures partagées
"""
import os
import pytest
from typing import Generator

# Forcer l'utilisation de l'environnement de test
os.environ["ENV"] = "test"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/15"
os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/15"
os.environ["UPLOAD_ALLOWED_EXTENSIONS"] = ".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
os.environ["UPLOAD_MAX_SIZE_MB"] = "10"
os.environ["UPLOAD_DIRECTORY"] = "/tmp/test_uploads"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["LOG_FILE_PATH"] = "/tmp/test_logs"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["TWO_FACTOR_ISSUER"] = "Test App"
os.environ["ENVIRONMENT"] = "test"

# Maintenant importer les modules qui dépendent de la config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


# Configuration de la base de données de test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la fonction get_db pour les tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db_engine():
    """Créer le moteur de base de données de test"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Créer une session de base de données pour chaque test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Créer un client de test FastAPI"""
    def override_get_db_for_test():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db_for_test
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user_data():
    """Données de test pour un utilisateur"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!@#",
        "full_name": "Test User",
        "role": "manager"
    }


# Configuration pour pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Définir la politique de boucle d'événements pour asyncio"""
    import asyncio
    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.get_event_loop_policy()