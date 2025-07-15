"""
Tests unitaires pour les fonctionnalités de sécurité
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
import secrets

from app.core.security import (
    create_access_token, verify_token, get_password_hash, verify_password,
    validate_password_strength, generate_refresh_token
)
from app.core.config import settings


class TestPasswordSecurity:
    """Tests pour la sécurité des mots de passe"""
    
    def test_password_hash_and_verify(self):
        """Test du hashage et de la vérification des mots de passe"""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)
    
    def test_password_strength_validation(self):
        """Test de la validation de la force des mots de passe"""
        # Mots de passe faibles
        weak_passwords = [
            ("short", "au moins 8 caractères"),
            ("alllowercase", "majuscule"),
            ("ALLUPPERCASE", "minuscule"),
            ("NoNumbers!", "chiffre"),
            ("NoSpecial123", "caractère spécial")
        ]
        
        for pwd, expected_msg in weak_passwords:
            valid, msg = validate_password_strength(pwd)
            assert not valid
            assert expected_msg in msg
        
        # Mots de passe forts
        strong_passwords = [
            "MySecure123!",
            "P@ssw0rd2024",
            "Str0ng&Secure!"
        ]
        
        for pwd in strong_passwords:
            valid, msg = validate_password_strength(pwd)
            assert valid
            assert msg == ""


class TestJWTTokens:
    """Tests pour les tokens JWT"""
    
    def test_create_and_verify_access_token(self):
        """Test de création et vérification des access tokens"""
        data = {"sub": "testuser", "cabinet_id": 1}
        token = create_access_token(data)
        
        assert token is not None
        
        # Vérifier le token
        from fastapi import HTTPException
        credentials_exception = HTTPException(status_code=401)
        username = verify_token(token, credentials_exception)
        
        assert username == "testuser"
    
    def test_expired_token(self):
        """Test avec un token expiré"""
        data = {"sub": "testuser"}
        # Créer un token expiré
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        from fastapi import HTTPException
        credentials_exception = HTTPException(status_code=401)
        
        with pytest.raises(HTTPException):
            verify_token(token, credentials_exception)
    
    def test_invalid_token(self):
        """Test avec un token invalide"""
        from fastapi import HTTPException
        credentials_exception = HTTPException(status_code=401)
        
        with pytest.raises(HTTPException):
            verify_token("invalid.token.here", credentials_exception)


class TestRefreshTokens:
    """Tests pour les refresh tokens"""
    
    def test_generate_refresh_token(self):
        """Test de génération de refresh token"""
        token1 = generate_refresh_token()
        token2 = generate_refresh_token()
        
        assert token1 != token2
        assert len(token1) > 20
        assert isinstance(token1, str)


@pytest.mark.asyncio
class TestTwoFactorAuth:
    """Tests pour l'authentification à deux facteurs"""
    
    async def test_totp_generation_and_verification(self):
        """Test de génération et vérification TOTP"""
        import pyotp
        
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # Le code actuel doit être valide
        current_code = totp.now()
        assert totp.verify(current_code, valid_window=1)
        
        # Un code aléatoire ne doit pas être valide
        random_code = "123456"
        assert not totp.verify(random_code, valid_window=1)
    
    async def test_backup_codes(self):
        """Test des codes de récupération"""
        from passlib.hash import pbkdf2_sha256
        
        # Générer des codes
        codes = []
        hashed_codes = []
        
        for _ in range(8):
            code = f"{secrets.randbelow(1000000):06d}"
            codes.append(code)
            hashed_codes.append(pbkdf2_sha256.hash(code))
        
        # Vérifier qu'un code est valide
        assert pbkdf2_sha256.verify(codes[0], hashed_codes[0])
        
        # Vérifier qu'un mauvais code n'est pas valide
        assert not pbkdf2_sha256.verify("000000", hashed_codes[0])