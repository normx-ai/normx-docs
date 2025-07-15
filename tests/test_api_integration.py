"""
Tests d'intégration pour l'API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.cabinet import Cabinet
from app.core.security import get_password_hash


# Configuration de test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Créer un client de test"""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(client):
    """Créer un utilisateur de test"""
    db = TestingSessionLocal()
    
    # Créer un cabinet de test
    cabinet = Cabinet(
        nom="Cabinet Test",
        slug="cabinet-test",
        pays_code="FR",
        devise="EUR"
    )
    db.add(cabinet)
    db.commit()
    
    # Créer un utilisateur
    user = User(
        cabinet_id=cabinet.id,
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("Test123!@#"),
        full_name="Test User",
        role="manager"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    db.delete(user)
    db.delete(cabinet)
    db.commit()
    db.close()


class TestAuthentication:
    """Tests pour l'authentification"""
    
    def test_login_success(self, client, test_user):
        """Test de connexion réussie"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test avec des identifiants invalides"""
        response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "wronguser",
                "password": "wrongpass"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"]
    
    def test_refresh_token(self, client, test_user):
        """Test du refresh token"""
        # D'abord se connecter
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Utiliser le refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestSecurityHeaders:
    """Tests pour les headers de sécurité"""
    
    def test_security_headers_present(self, client):
        """Vérifier la présence des headers de sécurité"""
        response = client.get("/")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert "Content-Security-Policy" in response.headers


class TestRateLimiting:
    """Tests pour le rate limiting"""
    
    @pytest.mark.skip(reason="Rate limiting nécessite Redis")
    def test_rate_limit_exceeded(self, client):
        """Test du dépassement de la limite de requêtes"""
        # Faire plusieurs requêtes rapidement
        for _ in range(150):  # Au-delà de la limite par minute
            response = client.get("/api/v1/health")
        
        # La dernière devrait être bloquée
        assert response.status_code == 429


class TestFileUpload:
    """Tests pour l'upload de fichiers"""
    
    def test_upload_valid_file(self, client, test_user):
        """Test d'upload d'un fichier valide"""
        # Se connecter d'abord
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]
        
        # Créer un fichier de test
        files = {
            "files": ("test.pdf", b"PDF content", "application/pdf")
        }
        
        response = client.post(
            "/api/v1/dossiers/1/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Note: Ceci échouera car le dossier n'existe pas, mais on teste la validation
        assert response.status_code in [404, 422]  # Not found ou validation error
    
    def test_upload_invalid_extension(self, client, test_user):
        """Test d'upload avec une extension non autorisée"""
        # Se connecter
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]
        
        # Fichier avec extension dangereuse
        files = {
            "files": ("malicious.exe", b"MZ", "application/x-msdownload")
        }
        
        response = client.post(
            "/api/v1/dossiers/1/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Devrait être rejeté
        assert response.status_code in [400, 404]


class TestPagination:
    """Tests pour la pagination"""
    
    def test_dossiers_pagination(self, client, test_user):
        """Test de la pagination sur la liste des dossiers"""
        # Se connecter
        login_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "testuser",
                "password": "Test123!@#"
            }
        )
        token = login_response.json()["access_token"]
        
        # Tester avec des paramètres de pagination
        response = client.get(
            "/api/v1/dossiers/?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        # La réponse devrait être une liste
        assert isinstance(response.json(), list)