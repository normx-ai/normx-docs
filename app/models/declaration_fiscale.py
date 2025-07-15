from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import date

from app.core.database import Base


class TypeDeclarationFiscale(str, enum.Enum):
    """Types de déclarations fiscales"""
    TVA = "TVA"  # Déclaration de TVA (mensuelle/trimestrielle)
    IS = "IS"  # Impôt sur les sociétés
    LIASSE_FISCALE = "LIASSE_FISCALE"  # Liasse fiscale annuelle
    CET = "CET"  # Contribution économique territoriale
    CFE = "CFE"  # Cotisation foncière des entreprises
    CVAE = "CVAE"  # Cotisation sur la valeur ajoutée des entreprises
    BIC = "BIC"  # Bénéfices industriels et commerciaux
    BNC = "BNC"  # Bénéfices non commerciaux
    MICRO_BIC = "MICRO_BIC"  # Micro-entreprise BIC
    MICRO_BNC = "MICRO_BNC"  # Micro-entreprise BNC


class StatutDeclarationFiscale(str, enum.Enum):
    """Statuts des déclarations fiscales"""
    A_FAIRE = "A_FAIRE"
    EN_COURS = "EN_COURS"
    PRETE = "PRETE"  # Prête à être télédéclarée
    TELEDECLAREE = "TELEDECLAREE"
    VALIDEE = "VALIDEE"  # Validée par l'administration


class RegimeDeclarationFiscale(str, enum.Enum):
    """Régimes de déclaration"""
    MENSUEL = "MENSUEL"
    TRIMESTRIEL = "TRIMESTRIEL"
    ANNUEL = "ANNUEL"


class DeclarationFiscale(Base):
    """Modèle pour les déclarations fiscales spécifiques aux dossiers FISCALITE"""
    __tablename__ = "declarations_fiscales"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    
    # Relation avec le dossier
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False)
    
    # Informations sur la déclaration
    type_declaration = Column(String(50), nullable=False)
    statut = Column(String(50), nullable=False, default='A_FAIRE')
    regime = Column(String(50), nullable=False)
    
    # Période concernée
    periode_debut = Column(Date, nullable=False)  # Début de période (ex: 2025-01-01)
    periode_fin = Column(Date, nullable=False)    # Fin de période (ex: 2025-01-31)
    date_limite = Column(Date, nullable=False)    # Date limite de déclaration
    
    # Montants calculés
    montant_base = Column(Numeric(12, 2), nullable=True)       # Base imposable
    montant_taxe = Column(Numeric(12, 2), nullable=True)       # Montant de la taxe
    montant_credit = Column(Numeric(12, 2), nullable=True)     # Crédit de taxe
    montant_a_payer = Column(Numeric(12, 2), nullable=True)    # Montant final à payer
    
    # Informations de télédéclaration
    numero_teledeclaration = Column(String, nullable=True)     # Numéro reçu après télédéclaration
    date_teledeclaration = Column(DateTime, nullable=True)     # Date de télédéclaration
    date_paiement = Column(Date, nullable=True)               # Date de paiement
    
    # Informations administratives
    formulaire_cerfa = Column(String, nullable=True)          # Numéro du formulaire CERFA
    observations = Column(Text, nullable=True)                # Observations particulières
    
    # Gestion des rectifications
    declaration_origine_id = Column(Integer, ForeignKey("declarations_fiscales.id"), nullable=True)
    est_rectificative = Column(Boolean, default=False)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relations
    cabinet = relationship("Cabinet", backref="declarations_fiscales")
    dossier = relationship("Dossier", backref="declarations_fiscales")
    declaration_origine = relationship("DeclarationFiscale", remote_side=[id], backref="rectifications")
    
    @property
    def libelle_periode(self) -> str:
        """Retourne un libellé lisible de la période"""
        if self.regime == RegimeDeclarationFiscale.MENSUEL:
            return f"{self.periode_debut.strftime('%B %Y').capitalize()}"
        elif self.regime == RegimeDeclarationFiscale.TRIMESTRIEL:
            trimestre = (self.periode_debut.month - 1) // 3 + 1
            return f"T{trimestre} {self.periode_debut.year}"
        else:  # ANNUEL
            return f"Année {self.periode_debut.year}"
    
    @property
    def est_en_retard(self) -> bool:
        """Vérifie si la déclaration est en retard"""
        if self.statut in [StatutDeclarationFiscale.TELEDECLAREE, StatutDeclarationFiscale.VALIDEE]:
            return False
        return date.today() > self.date_limite
    
    @property
    def jours_avant_echeance(self) -> int:
        """Retourne le nombre de jours avant l'échéance"""
        return (self.date_limite - date.today()).days
    
    @property
    def priorite_calculee(self) -> str:
        """Calcule la priorité selon la proximité de l'échéance"""
        if self.est_en_retard:
            return "URGENTE"
        elif self.jours_avant_echeance <= 3:
            return "HAUTE"
        elif self.jours_avant_echeance <= 7:
            return "NORMALE"
        else:
            return "BASSE"
    
    def __repr__(self):
        return f"<DeclarationFiscale(type={self.type_declaration}, periode={self.libelle_periode}, statut={self.statut})>"