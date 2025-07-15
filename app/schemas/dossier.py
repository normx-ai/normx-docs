from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime
from app.models.dossier import StatusDossier, TypeDossier, PrioriteDossier
from app.schemas.echeance import Echeance


class DossierBase(BaseModel):
    nom_client: str
    type_dossier: TypeDossier
    date_echeance: Optional[date] = None
    responsable_id: Optional[int] = None
    description: Optional[str] = None
    priorite: Optional[PrioriteDossier] = PrioriteDossier.NORMALE
    services_list: List[str] = []
    
    # Informations client
    type_entreprise: Optional[str] = None
    numero_siret: Optional[str] = None
    periode_comptable: Optional[str] = None
    exercice_fiscal: Optional[str] = None
    contact_client: Optional[str] = None
    telephone_client: Optional[str] = None


class DossierCreate(DossierBase):
    reference: Optional[str] = None
    notes: Optional[str] = None


class DossierUpdate(BaseModel):
    nom_client: Optional[str] = None
    type_dossier: Optional[TypeDossier] = None
    statut: Optional[StatusDossier] = None
    date_echeance: Optional[date] = None
    responsable_id: Optional[int] = None
    description: Optional[str] = None
    priorite: Optional[PrioriteDossier] = None
    services_list: Optional[List[str]] = None
    notes: Optional[str] = None
    
    # Informations client
    type_entreprise: Optional[str] = None
    numero_siret: Optional[str] = None
    periode_comptable: Optional[str] = None
    exercice_fiscal: Optional[str] = None
    contact_client: Optional[str] = None
    telephone_client: Optional[str] = None


class DossierStatusUpdate(BaseModel):
    statut: StatusDossier
    commentaire: Optional[str] = None


class Dossier(DossierBase):
    id: int
    reference: str
    statut: StatusDossier
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class DossierWithDetails(Dossier):
    responsable_name: Optional[str] = None
    alerts_count: int = 0
    documents_count: int = 0
    echeances: List[Echeance] = []
    prochaine_echeance_date: Optional[date] = None
    echeances_completees: int = 0
    echeances_totales: int = 0


class DailyPoint(BaseModel):
    date: date
    dossiers_urgents: List[DossierWithDetails]
    dossiers_retard: List[DossierWithDetails]
    dossiers_a_traiter: List[DossierWithDetails]
    dossiers_completes: List[DossierWithDetails]
    statistiques: dict