from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    cabinet_name: Optional[str] = None
    role: str = "collaborateur"


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    cabinet_name: Optional[str] = None
    role: str = "collaborateur"
    # Nouveaux champs pour la création du cabinet
    pays_code: Optional[str] = "FR"
    siret: Optional[str] = None
    telephone_cabinet: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    cabinet_name: Optional[str] = None
    role: Optional[str] = None


class CabinetSettings(BaseModel):
    cabinet_name: Optional[str] = None
    siret: Optional[str] = None
    siren: Optional[str] = None
    nom_gerant: Optional[str] = None
    adresse_cabinet: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    telephone_cabinet: Optional[str] = None
    email_cabinet: Optional[str] = None
    site_web: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    username: Optional[str] = None