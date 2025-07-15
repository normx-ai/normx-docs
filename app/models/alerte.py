from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TypeAlerte(str, enum.Enum):
    RETARD = "retard"
    DEADLINE_PROCHE = "deadline_proche"
    DOCUMENT_MANQUANT = "document_manquant"
    ACTION_REQUISE = "action_requise"
    RAPPEL = "rappel"


class NiveauAlerte(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"


class Alerte(Base):
    __tablename__ = "alertes"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"))
    type_alerte = Column(Enum(TypeAlerte), nullable=False)
    niveau = Column(Enum(NiveauAlerte), default=NiveauAlerte.INFO)
    message = Column(Text, nullable=False)
    active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolution_note = Column(Text)
    
    # Relations
    cabinet = relationship("Cabinet", backref="alertes")
    dossier = relationship("Dossier", back_populates="alertes")