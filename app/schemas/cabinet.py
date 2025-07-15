"""
Schémas Pydantic pour le modèle Cabinet
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CabinetBase(BaseModel):
    nom: str = Field(..., description="Nom du cabinet")
    siret: Optional[str] = Field(None, max_length=14)
    siren: Optional[str] = Field(None, max_length=9)
    numero_tva: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = Field(None, max_length=5)
    ville: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    pays_code: str = Field(default="FR", max_length=2, description="Code ISO du pays")
    langue: str = Field(default="fr-FR", max_length=5)
    fuseau_horaire: str = Field(default="Europe/Paris", max_length=50)


class CabinetCreate(CabinetBase):
    """Schéma pour la création d'un cabinet"""
    pass


class CabinetUpdate(BaseModel):
    """Schéma pour la mise à jour d'un cabinet"""
    nom: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    numero_tva: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    pays_code: Optional[str] = None
    langue: Optional[str] = None
    fuseau_horaire: Optional[str] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = None
    max_clients: Optional[int] = None
    plan: Optional[str] = None


class CabinetResponse(CabinetBase):
    """Schéma pour la réponse d'un cabinet"""
    id: int
    slug: str
    is_active: bool
    max_users: int
    max_clients: int
    plan: str
    devise: str
    format_date: str
    date_expiration: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Statistiques
    user_count: Optional[int] = 0
    client_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class CabinetRegistration(BaseModel):
    """Schéma pour l'inscription complète (cabinet + utilisateur admin)"""
    # Informations du cabinet
    cabinet_name: str = Field(..., description="Nom du cabinet")
    pays_code: str = Field(..., description="Code ISO du pays (ex: FR, CM, SN)")
    siret: Optional[str] = Field(None, description="Identifiant d'entreprise selon le pays")
    telephone_cabinet: Optional[str] = Field(None, description="Téléphone du cabinet")
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    
    # Informations de l'utilisateur admin
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Email de l'administrateur")
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., description="Nom complet de l'administrateur")
    telephone_user: Optional[str] = Field(None, description="Téléphone de l'utilisateur")


class RegistrationResponse(BaseModel):
    """Réponse après inscription réussie"""
    cabinet: CabinetResponse
    user: dict
    access_token: str
    token_type: str = "bearer"
    message: str = "Inscription réussie"