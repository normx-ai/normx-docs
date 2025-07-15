from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Enum, Table, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import date, timedelta

from app.core.database import Base


class StatusDossier(str, enum.Enum):
    NOUVEAU = "NOUVEAU"
    EN_COURS = "EN_COURS"
    EN_ATTENTE = "EN_ATTENTE"
    COMPLETE = "COMPLETE"
    ARCHIVE = "ARCHIVE"


class TypeDossier(str, enum.Enum):
    COMPTABILITE = "COMPTABILITE"
    FISCALITE = "FISCALITE"
    PAIE = "PAIE"
    JURIDIQUE = "JURIDIQUE"
    AUDIT = "AUDIT"
    CONSEIL = "CONSEIL"
    AUTRE = "AUTRE"


class PrioriteDossier(str, enum.Enum):
    BASSE = "BASSE"
    NORMALE = "NORMALE"
    HAUTE = "HAUTE"
    URGENTE = "URGENTE"


class Dossier(Base):
    __tablename__ = "dossiers"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    reference = Column(String, nullable=False, index=True)  # Unique par cabinet
    nom_client = Column(String, nullable=False, index=True)
    # client_id = Column(Integer, ForeignKey("clients.id"))  # Commenté car le modèle Client n'existe pas
    
    # Stockage des services multiples comme JSON array
    services_list = Column(JSON, nullable=False, default=list)  # ["COMPTABILITE", "TVA", "PAIE"]
    
    type_dossier = Column(Enum(TypeDossier), nullable=False)  # Service principal
    statut = Column(Enum(StatusDossier), default=StatusDossier.NOUVEAU)
    date_echeance = Column(Date, nullable=True, index=True)
    responsable_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    priorite = Column(Enum(PrioriteDossier), default=PrioriteDossier.NORMALE)
    
    # Informations additionnelles
    description = Column(Text)
    notes = Column(Text)
    
    # Informations client
    type_entreprise = Column(String)  # SARL, SAS, EI, etc.
    numero_siret = Column(String)
    periode_comptable = Column(String)  # Mensuel, Trimestriel, Annuel
    exercice_fiscal = Column(String)  # 2023, 2024, etc.
    contact_client = Column(String)
    telephone_client = Column(String)
    
    # Lien avec l'utilisateur
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relations
    cabinet = relationship("Cabinet", back_populates="dossiers")
    responsable = relationship("User", foreign_keys=[responsable_id], backref="dossiers_responsable")
    user = relationship("User", foreign_keys=[user_id], backref="dossiers_created")
    # client = relationship("Client", backref="dossiers")  # Commenté car le modèle Client n'existe pas
    alertes = relationship("Alerte", back_populates="dossier")
    historique = relationship("HistoriqueDossier", back_populates="dossier")
    # services = relationship("Service", secondary="dossier_services", back_populates="dossiers")  # Table n'existe pas encore
    echeances = relationship("Echeance", back_populates="dossier", cascade="all, delete-orphan")
    # declarations_fiscales = relationship("DeclarationFiscale", back_populates="dossier", cascade="all, delete-orphan")
    
    # Contrainte unique pour reference par cabinet
    __table_args__ = (
        UniqueConstraint('cabinet_id', 'reference', name='uq_dossier_cabinet_reference'),
    )
    
    @property
    def prochaine_echeance(self):
        """Retourne la prochaine échéance non complétée"""
        if not self.echeances:
            return None
        
        from datetime import date
        today = date.today()
        
        # Trouver la prochaine échéance non complétée
        echeances_a_faire = [e for e in self.echeances if e.statut != 'COMPLETE']
        if not echeances_a_faire:
            return None
        
        # Trier par date d'échéance
        echeances_a_faire.sort(key=lambda e: e.date_echeance)
        
        # Retourner la première échéance à venir ou en retard
        for echeance in echeances_a_faire:
            if echeance.date_echeance >= today or echeance.statut == 'EN_RETARD':
                return echeance
        
        # Si toutes sont passées, retourner la dernière
        return echeances_a_faire[-1]
    
    @property
    def priorite_automatique(self) -> PrioriteDossier:
        """Calcule automatiquement la priorité selon la prochaine échéance et l'état des tâches"""
        if self.statut == StatusDossier.COMPLETE:
            return PrioriteDossier.NORMALE
        
        today = date.today()
        
        # Vérifier s'il y a des échéances en retard non complétées
        has_overdue = False
        if hasattr(self, 'echeances') and self.echeances:
            for echeance in self.echeances:
                if echeance.date_echeance < today and echeance.statut != 'COMPLETE':
                    has_overdue = True
                    break
        
        # Si dossier FISCALITE, vérifier aussi les déclarations en retard
        # TODO: Réactiver quand la relation declarations_fiscales sera correctement configurée
        # if self.type_dossier == 'FISCALITE' and hasattr(self, 'declarations_fiscales'):
        #     for declaration in self.declarations_fiscales:
        #         if declaration.date_limite < today and declaration.statut not in ['TELEDECLAREE', 'VALIDEE']:
        #             has_overdue = True
        #             break
        
        # Si des tâches sont en retard, priorité URGENTE
        if has_overdue:
            return PrioriteDossier.URGENTE
        
        # Sinon, utiliser la prochaine échéance pour calculer la priorité
        prochaine = self.prochaine_echeance
        if prochaine:
            date_reference = prochaine.date_echeance
        elif self.date_echeance:
            date_reference = self.date_echeance
        else:
            return PrioriteDossier.NORMALE
            
        jours_restants = (date_reference - today).days
        
        if jours_restants < 0:  # En retard
            return PrioriteDossier.URGENTE
        elif jours_restants <= 2:  # Dans 0-2 jours  
            return PrioriteDossier.HAUTE
        elif jours_restants <= 7:  # Dans 3-7 jours
            return PrioriteDossier.NORMALE
        else:  # Plus de 7 jours
            return PrioriteDossier.BASSE
    
    @property
    def derniere_activite(self):
        """Retourne la date de dernière activité (dernière modification d'historique)"""
        if self.historique:
            return max(h.created_at for h in self.historique)
        return self.created_at
    
    def peut_passer_en_cours(self) -> bool:
        """Vérifie si le dossier peut passer automatiquement en cours"""
        return self.statut == StatusDossier.NOUVEAU
    
    def peut_passer_en_attente(self) -> bool:
        """Vérifie si le dossier peut passer en attente (pas d'activité depuis 7 jours)"""
        if self.statut != StatusDossier.EN_COURS:
            return False
        from datetime import datetime, timedelta, timezone
        seuil = datetime.now(timezone.utc) - timedelta(days=7)
        # S'assurer que derniere_activite est timezone-aware
        derniere = self.derniere_activite
        if derniere.tzinfo is None:
            derniere = derniere.replace(tzinfo=timezone.utc)
        return derniere < seuil
    
    def peut_passer_complete(self) -> bool:
        """Vérifie si le dossier peut être marqué comme complété"""
        # TODO: Ajouter la logique selon les documents requis, etc.
        return self.statut in [StatusDossier.EN_COURS, StatusDossier.EN_ATTENTE]