from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class TypeDocument(str, enum.Enum):
    FACTURE_ACHAT = "FACTURE_ACHAT"
    RELEVE_BANCAIRE = "RELEVE_BANCAIRE"
    FACTURE_VENTE = "FACTURE_VENTE"
    ETAT_PAIE = "ETAT_PAIE"
    DECLARATION_IMPOT = "DECLARATION_IMPOT"
    DECLARATION_TVA = "DECLARATION_TVA"
    DECLARATION_SOCIALE = "DECLARATION_SOCIALE"
    CONTRAT = "CONTRAT"
    COURRIER = "COURRIER"
    AUTRE = "AUTRE"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    nom = Column(String, nullable=False)  # Nom original du fichier
    nom_fichier_stockage = Column(String, nullable=False)  # Nom sécurisé pour le stockage
    type = Column(Enum(TypeDocument), nullable=False)
    chemin_fichier = Column(String, nullable=False)  # Chemin du fichier sur le serveur
    url = Column(String)  # URL pour accéder au fichier
    taille = Column(Integer)  # Taille en octets
    mime_type = Column(String)  # Type MIME vérifié
    hash_fichier = Column(String)  # Hash SHA256 pour l'intégrité
    
    # Relations
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    echeance_id = Column(Integer, ForeignKey("echeances.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Qui a uploadé
    
    # Informations temporelles
    mois = Column(Integer)  # 1-12
    annee = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    cabinet = relationship("Cabinet", backref="documents")
    dossier = relationship("Dossier", backref="documents")
    echeance = relationship("Echeance", backref="documents")
    user = relationship("User", backref="documents_uploaded")