"""
Schémas Pydantic pour l'authentification à deux facteurs
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TwoFactorSetup(BaseModel):
    """Réponse lors de la configuration initiale du 2FA"""
    secret: str
    qr_code: str = Field(..., description="QR code en base64")
    backup_codes: List[str] = Field(..., description="Codes de récupération")


class TwoFactorEnable(BaseModel):
    """Données pour activer le 2FA"""
    token: str = Field(..., min_length=6, max_length=6, description="Code TOTP à 6 chiffres")


class TwoFactorVerify(BaseModel):
    """Vérification d'un code 2FA"""
    token: str = Field(..., description="Code TOTP ou code de récupération")


class TwoFactorBackupCodes(BaseModel):
    """Liste des codes de récupération"""
    backup_codes: List[str]


class TwoFactorStatus(BaseModel):
    """Statut de l'authentification à deux facteurs"""
    enabled: bool
    activated_at: Optional[datetime] = None


class TwoFactorLoginChallenge(BaseModel):
    """Challenge 2FA lors de la connexion"""
    session_token: str = Field(..., description="Token de session temporaire")
    requires_2fa: bool = True


class TwoFactorLoginVerify(BaseModel):
    """Vérification du code 2FA lors de la connexion"""
    session_token: str
    token: str = Field(..., description="Code TOTP ou code de récupération")