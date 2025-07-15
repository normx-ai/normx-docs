"""
Tests pour la validation et l'upload sécurisé de fichiers
"""
import pytest
import os
import tempfile
from fastapi import UploadFile, HTTPException
from io import BytesIO
import asyncio

from app.core.file_validator import FileValidator, file_validator


class TestFileValidator:
    """Tests pour le validateur de fichiers"""
    
    @pytest.fixture
    def validator(self):
        """Créer une instance du validateur"""
        return FileValidator(max_size_mb=1)
    
    @pytest.mark.asyncio
    async def test_valid_file_extension(self, validator):
        """Test avec une extension valide"""
        # Créer un fichier factice
        file_content = b"Test PDF content"
        file = UploadFile(
            filename="test.pdf",
            file=BytesIO(file_content)
        )
        
        # La validation devrait réussir
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_content)
            tmp.flush()
            os.unlink(tmp.name)
    
    @pytest.mark.asyncio
    async def test_invalid_file_extension(self, validator):
        """Test avec une extension non autorisée"""
        file = UploadFile(
            filename="malicious.exe",
            file=BytesIO(b"MZ")  # Header d'exécutable Windows
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate_file(file, check_content=False)
        
        assert exc_info.value.status_code == 400
        assert "Extension de fichier non autorisée" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_file_size_limit(self, validator):
        """Test de la limite de taille"""
        # Créer un fichier de 2MB (limite est 1MB)
        large_content = b"X" * (2 * 1024 * 1024)
        file = UploadFile(
            filename="large.pdf",
            file=BytesIO(large_content)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await validator.validate_file(file, check_content=False)
        
        assert exc_info.value.status_code == 413
        assert "trop volumineux" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_dangerous_file_signature(self, validator):
        """Test de détection de signatures dangereuses"""
        # Fichier avec signature d'exécutable
        dangerous_content = b"MZ\x90\x00\x03"  # Header PE
        file = UploadFile(
            filename="fake.pdf",
            file=BytesIO(dangerous_content)
        )
        
        # Créer un fichier temporaire pour le test
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(dangerous_content)
            tmp.flush()
            
            # Mock de file_validator avec le fichier temporaire
            file._file = open(tmp.name, 'rb')
            
            try:
                with pytest.raises(HTTPException) as exc_info:
                    await validator.validate_file(file, check_content=True)
                
                assert exc_info.value.status_code == 400
                assert "dangereux" in str(exc_info.value.detail)
            finally:
                file._file.close()
                os.unlink(tmp.name)
    
    def test_safe_filename_generation(self, validator):
        """Test de génération de noms de fichiers sécurisés"""
        dangerous_names = [
            "../../../etc/passwd",
            "file<script>.pdf",
            "file name with spaces.pdf",
            "très_long_nom_de_fichier_qui_devrait_être_tronqué_pour_éviter_les_problèmes.pdf"
        ]
        
        for name in dangerous_names:
            safe_name = validator._generate_safe_filename(name)
            
            # Vérifier que le nom est sécurisé
            assert ".." not in safe_name
            assert "<" not in safe_name
            assert ">" not in safe_name
            assert len(safe_name) < 100
            assert safe_name.endswith(".pdf")
    
    def test_file_hash_calculation(self):
        """Test du calcul de hash de fichier"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = b"Test content for hashing"
            tmp.write(content)
            tmp.flush()
            
            try:
                hash1 = FileValidator.calculate_file_hash(tmp.name)
                hash2 = FileValidator.calculate_file_hash(tmp.name)
                
                # Le même fichier doit avoir le même hash
                assert hash1 == hash2
                assert len(hash1) == 64  # SHA256 = 64 caractères hex
            finally:
                os.unlink(tmp.name)