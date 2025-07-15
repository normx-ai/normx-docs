from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.document import TypeDocument


class DocumentBase(BaseModel):
    nom: str
    type: TypeDocument
    mois: int
    annee: int


class DocumentCreate(DocumentBase):
    echeance_id: Optional[int] = None


class DocumentUpdate(BaseModel):
    nom: Optional[str] = None
    type: Optional[TypeDocument] = None
    mois: Optional[int] = None
    annee: Optional[int] = None


class Document(DocumentBase):
    id: int
    chemin_fichier: str
    url: Optional[str] = None
    taille: Optional[int] = None
    dossier_id: int
    echeance_id: Optional[int] = None
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentWithDetails(Document):
    dossier_nom: Optional[str] = None
    uploaded_by: Optional[str] = None