from typing import Optional
from pydantic import BaseModel
from datetime import datetime, date
from enum import Enum


class TypeAlerteEnum(str, Enum):
    RETARD = "retard"
    DEADLINE_PROCHE = "deadline_proche"
    DOCUMENT_MANQUANT = "document_manquant"
    ACTION_REQUISE = "action_requise"
    RAPPEL = "rappel"


class NiveauAlerteEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"


class AlerteBase(BaseModel):
    dossier_id: int
    type_alerte: TypeAlerteEnum
    niveau: NiveauAlerteEnum
    message: str


class AlerteCreate(AlerteBase):
    pass


class AlerteResolve(BaseModel):
    resolution_note: Optional[str] = None


class Alerte(AlerteBase):
    id: int
    active: bool
    created_at: datetime
    resolved_at: Optional[datetime]
    resolution_note: Optional[str]
    
    class Config:
        from_attributes = True


class AlerteWithDossier(Alerte):
    dossier_client_name: str
    dossier_type: str
    dossier_deadline: date


class AlerteDashboard(BaseModel):
    alertes_urgentes: list[AlerteWithDossier]
    alertes_retard: list[AlerteWithDossier]
    alertes_documents_manquants: list[AlerteWithDossier]
    statistiques: dict