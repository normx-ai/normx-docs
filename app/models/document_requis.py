from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.models.document import TypeDocument


class DocumentRequis(Base):
    __tablename__ = "documents_requis"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    echeance_id = Column(Integer, ForeignKey("echeances.id"), nullable=False)
    type_document = Column(Enum(TypeDocument), nullable=False)
    mois = Column(Integer, nullable=False)
    annee = Column(Integer, nullable=False)
    est_applicable = Column(Boolean, default=True)
    est_fourni = Column(Boolean, default=False)
    
    # Relations
    cabinet = relationship("Cabinet", backref="documents_requis")
    dossier = relationship("Dossier", backref="documents_requis")
    echeance = relationship("Echeance", backref="documents_requis")