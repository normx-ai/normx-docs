from typing import Optional
from pydantic import BaseModel
from datetime import date, datetime


class EcheanceBase(BaseModel):
    mois: int
    annee: int
    periode_label: str
    date_echeance: date
    statut: str = "A_FAIRE"
    notes: Optional[str] = None


class EcheanceCreate(EcheanceBase):
    dossier_id: int


class EcheanceUpdate(BaseModel):
    statut: Optional[str] = None
    notes: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_completion: Optional[datetime] = None


class Echeance(EcheanceBase):
    id: int
    dossier_id: int
    date_debut: Optional[datetime] = None
    date_completion: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True