from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.alerte import Alerte, TypeAlerte, NiveauAlerte
from app.models.dossier import Dossier


class AlerteService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_alerte(
        self,
        dossier_id: int,
        type_alerte: TypeAlerte,
        message: str,
        niveau: NiveauAlerte = NiveauAlerte.INFO
    ) -> Alerte:
        """Créer une nouvelle alerte"""
        alerte = Alerte(
            dossier_id=dossier_id,
            type_alerte=type_alerte,
            message=message,
            niveau=niveau,
            active=True
        )
        self.db.add(alerte)
        self.db.flush()
        return alerte
    
    def check_existing_alert(
        self,
        dossier_id: int,
        type_alerte: TypeAlerte,
        days_back: int = 1
    ) -> bool:
        """Vérifier si une alerte similaire existe déjà récemment"""
        since_date = datetime.now() - timedelta(days=days_back)
        
        existing = self.db.query(Alerte).filter(
            and_(
                Alerte.dossier_id == dossier_id,
                Alerte.type_alerte == type_alerte,
                Alerte.created_at >= since_date,
                Alerte.active == True
            )
        ).first()
        
        return existing is not None
    
    def create_alerte_retard(self, dossier: Dossier) -> bool:
        """Créer une alerte de retard si elle n'existe pas déjà"""
        if self.check_existing_alert(dossier.id, TypeAlerte.RETARD):
            return False
        
        jours_retard = (date.today() - dossier.deadline).days
        message = f"Le dossier {dossier.client_name} - {dossier.type_dossier.value} a {jours_retard} jour(s) de retard"
        
        self.create_alerte(
            dossier_id=dossier.id,
            type_alerte=TypeAlerte.RETARD,
            message=message,
            niveau=NiveauAlerte.URGENT if jours_retard > 5 else NiveauAlerte.WARNING
        )
        return True
    
    def create_alerte_deadline_proche(self, dossier: Dossier) -> bool:
        """Créer une alerte de deadline proche"""
        if self.check_existing_alert(dossier.id, TypeAlerte.DEADLINE_PROCHE):
            return False
        
        jours_restants = (dossier.deadline - date.today()).days
        message = f"Deadline proche: {dossier.client_name} - {dossier.type_dossier.value} dans {jours_restants} jour(s)"
        
        self.create_alerte(
            dossier_id=dossier.id,
            type_alerte=TypeAlerte.DEADLINE_PROCHE,
            message=message,
            niveau=NiveauAlerte.WARNING
        )
        return True
    
    def create_alerte_inactivite(self, dossier: Dossier) -> bool:
        """Créer une alerte d'inactivité"""
        if self.check_existing_alert(dossier.id, TypeAlerte.ACTION_REQUISE, days_back=7):
            return False
        
        jours_inactivite = (datetime.now() - dossier.updated_at).days
        message = f"Aucune activité depuis {jours_inactivite} jours sur le dossier {dossier.client_name}"
        
        self.create_alerte(
            dossier_id=dossier.id,
            type_alerte=TypeAlerte.ACTION_REQUISE,
            message=message,
            niveau=NiveauAlerte.INFO
        )
        return True
    
    def resolve_alerte(self, alerte_id: int, resolution_note: Optional[str] = None) -> Alerte:
        """Résoudre une alerte"""
        alerte = self.db.query(Alerte).filter(Alerte.id == alerte_id).first()
        if alerte:
            alerte.active = False
            alerte.resolved_at = datetime.now()
            alerte.resolution_note = resolution_note
            self.db.flush()
        return alerte
    
    def get_active_alerts_for_user(self, user_id: int) -> List[Alerte]:
        """Récupérer les alertes actives pour un utilisateur"""
        return self.db.query(Alerte).join(Dossier).filter(
            and_(
                Alerte.active == True,
                Dossier.responsable_id == user_id
            )
        ).order_by(Alerte.niveau.desc(), Alerte.created_at.desc()).all()
    
    def creer_alerte_document_manquant(
        self,
        dossier_id: int,
        type_document: str,
        echeance_id: Optional[int] = None
    ) -> bool:
        """Créer une alerte pour un document manquant"""
        # Vérifier si une alerte similaire existe déjà
        if self.check_existing_alert(dossier_id, TypeAlerte.DOCUMENT_MANQUANT):
            return False
        
        dossier = self.db.query(Dossier).filter(Dossier.id == dossier_id).first()
        if not dossier:
            return False
        
        message = f"Document manquant: {type_document} pour le dossier {dossier.nom_client}"
        
        self.create_alerte(
            dossier_id=dossier_id,
            type_alerte=TypeAlerte.DOCUMENT_MANQUANT,
            message=message,
            niveau=NiveauAlerte.WARNING
        )
        return True