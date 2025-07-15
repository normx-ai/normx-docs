from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Echeance(Base):
    __tablename__ = "echeances"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    
    # Période concernée
    mois = Column(Integer, nullable=False)  # 1-12
    annee = Column(Integer, nullable=False)  # 2025
    periode_label = Column(String, nullable=False)  # "Janvier 2025"
    
    # Date d'échéance calculée
    date_echeance = Column(Date, nullable=False, index=True)
    
    # Statut de l'échéance
    statut = Column(String, default="A_FAIRE")  # A_FAIRE, EN_COURS, COMPLETE, EN_RETARD
    
    # Dates de suivi
    date_debut = Column(DateTime(timezone=True))
    date_completion = Column(DateTime(timezone=True))
    
    # Notes spécifiques à cette échéance
    notes = Column(Text)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    cabinet = relationship("Cabinet", backref="echeances")
    dossier = relationship("Dossier", back_populates="echeances")