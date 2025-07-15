from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SaisieComptable(Base):
    __tablename__ = "saisies_comptables"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    
    # Relations
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    echeance_id = Column(Integer, ForeignKey("echeances.id"), nullable=False)
    
    # Type de journal
    type_journal = Column(String, nullable=False)  # BANQUE, CAISSE, OD, ACHATS, VENTES, PAIE
    
    # Statut
    est_complete = Column(Boolean, default=False)
    date_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Informations temporelles
    mois = Column(Integer, nullable=False)  # 1-12
    annee = Column(Integer, nullable=False)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relations
    cabinet = relationship("Cabinet", backref="saisies")
    dossier = relationship("Dossier", backref="saisies")
    echeance = relationship("Echeance", backref="saisies")
    completed_by = relationship("User")