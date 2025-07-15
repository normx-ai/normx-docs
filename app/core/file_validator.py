"""
Module de validation sécurisée des fichiers uploadés
"""
import os
import hashlib
import mimetypes
import magic
from pathlib import Path
from typing import Optional, Set, Tuple
from fastapi import UploadFile, HTTPException
import aiofiles
import uuid


class FileValidator:
    """Validateur de fichiers avec vérifications de sécurité"""
    
    # Extensions autorisées par type de document
    ALLOWED_EXTENSIONS: Set[str] = {
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.odt', '.ods',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        # Texte
        '.txt', '.csv',
        # Archives (avec précaution)
        '.zip', '.rar', '.7z'
    }
    
    # Types MIME autorisés
    ALLOWED_MIMETYPES: Set[str] = {
        # PDF
        'application/pdf',
        # Microsoft Office
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        # OpenDocument
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet',
        # Images
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        # Texte
        'text/plain',
        'text/csv',
        # Archives
        'application/zip',
        'application/x-rar-compressed',
        'application/x-7z-compressed'
    }
    
    # Signatures de fichiers (magic numbers) dangereuses
    DANGEROUS_SIGNATURES = [
        b'MZ',  # Exécutables Windows
        b'\x7fELF',  # Exécutables Linux
        b'#!/',  # Scripts shell
        b'#!',  # Scripts
        b'<?php',  # Scripts PHP
        b'<script',  # JavaScript dans HTML
    ]
    
    def __init__(
        self,
        max_size_mb: int = 10,
        allowed_extensions: Optional[Set[str]] = None,
        allowed_mimetypes: Optional[Set[str]] = None
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or self.ALLOWED_EXTENSIONS
        self.allowed_mimetypes = allowed_mimetypes or self.ALLOWED_MIMETYPES
        
        # Initialiser python-magic
        self.mime_detector = magic.Magic(mime=True)
    
    async def validate_file(
        self,
        file: UploadFile,
        check_content: bool = True
    ) -> Tuple[str, str, int]:
        """
        Valide un fichier uploadé
        
        Args:
            file: Fichier uploadé
            check_content: Vérifier le contenu du fichier
            
        Returns:
            Tuple (nom_sécurisé, type_mime, taille)
            
        Raises:
            HTTPException: Si le fichier ne passe pas la validation
        """
        
        # 1. Vérifier que le fichier existe
        if not file or not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Aucun fichier fourni"
            )
        
        # 2. Vérifier l'extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Extension de fichier non autorisée: {file_ext}"
            )
        
        # 3. Vérifier la taille (lecture par chunks pour éviter OOM)
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        # Sauvegarder temporairement pour analyse
        temp_path = f"/tmp/{uuid.uuid4()}"
        
        try:
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    
                    file_size += len(chunk)
                    
                    # Vérifier la taille au fur et à mesure
                    if file_size > self.max_size_bytes:
                        raise HTTPException(
                            status_code=413,
                            detail=f"Fichier trop volumineux. Maximum: {self.max_size_bytes / 1024 / 1024}MB"
                        )
                    
                    await temp_file.write(chunk)
            
            # 4. Vérifier le type MIME réel (pas juste l'extension)
            if check_content:
                detected_mime = self.mime_detector.from_file(temp_path)
                
                if detected_mime not in self.allowed_mimetypes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Type de fichier non autorisé: {detected_mime}"
                    )
                
                # 5. Vérifier les signatures dangereuses
                with open(temp_path, 'rb') as f:
                    file_header = f.read(1024)  # Lire les premiers 1KB
                    
                    for signature in self.DANGEROUS_SIGNATURES:
                        if file_header.startswith(signature):
                            raise HTTPException(
                                status_code=400,
                                detail="Fichier potentiellement dangereux détecté"
                            )
            
            # 6. Générer un nom de fichier sécurisé
            safe_filename = self._generate_safe_filename(file.filename)
            
            # 7. Réinitialiser le curseur du fichier
            await file.seek(0)
            
            # Nettoyer le fichier temporaire
            os.unlink(temp_path)
            
            return safe_filename, detected_mime if check_content else "", file_size
            
        except HTTPException:
            # Nettoyer et relancer l'exception
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
        except Exception as e:
            # Nettoyer et transformer en HTTPException
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la validation du fichier: {str(e)}"
            )
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """
        Génère un nom de fichier sécurisé
        
        Args:
            original_filename: Nom de fichier original
            
        Returns:
            Nom de fichier sécurisé
        """
        # Extraire l'extension
        path = Path(original_filename)
        extension = path.suffix.lower()
        base_name = path.stem
        
        # Supprimer les caractères dangereux
        import re
        safe_base = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
        safe_base = safe_base[:50]  # Limiter la longueur
        
        # Générer un identifiant unique
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Construire le nom final
        safe_filename = f"{timestamp}_{unique_id}_{safe_base}{extension}"
        
        return safe_filename
    
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calcule le hash d'un fichier
        
        Args:
            file_path: Chemin du fichier
            algorithm: Algorithme de hash (sha256, md5, etc.)
            
        Returns:
            Hash hexadécimal du fichier
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()


# Instance globale du validateur
file_validator = FileValidator()


# Fonction helper pour utilisation dans les endpoints
async def validate_upload(
    file: UploadFile,
    max_size_mb: Optional[int] = None,
    allowed_extensions: Optional[Set[str]] = None
) -> Tuple[str, str, int]:
    """
    Valide un fichier uploadé avec des paramètres personnalisés
    
    Args:
        file: Fichier uploadé
        max_size_mb: Taille maximale en MB
        allowed_extensions: Extensions autorisées
        
    Returns:
        Tuple (nom_sécurisé, type_mime, taille)
    """
    validator = FileValidator(
        max_size_mb=max_size_mb or 10,
        allowed_extensions=allowed_extensions
    )
    
    return await validator.validate_file(file)


from datetime import datetime