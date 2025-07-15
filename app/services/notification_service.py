"""
Service de gestion des notifications
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.dossier import Dossier, StatusDossier
from app.models.echeance import Echeance
from app.models.document_requis import DocumentRequis
from app.models.notification import Notification
from app.models.alerte import Alerte, TypeAlerte, NiveauAlerte
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class NotificationService:
    
    @staticmethod
    async def check_and_send_notifications(db: Session, cabinet_id: int):
        """
        Vérifie et envoie toutes les notifications nécessaires pour un cabinet
        """
        try:
            # 1. Notifications d'échéances proches
            await NotificationService._check_echeances_proches(db, cabinet_id)
            
            # 2. Notifications de documents manquants
            await NotificationService._check_documents_manquants(db, cabinet_id)
            
            # 3. Notifications de tâches en retard
            await NotificationService._check_taches_retard(db, cabinet_id)
            
            logger.info(f"Vérification des notifications terminée pour le cabinet {cabinet_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des notifications: {str(e)}")
    
    @staticmethod
    async def _check_echeances_proches(db: Session, cabinet_id: int):
        """Vérifie les échéances proches (dans les 7 prochains jours)"""
        today = date.today()
        deadline = today + timedelta(days=7)
        
        # Récupérer les échéances proches
        echeances = db.query(Echeance).join(Dossier).filter(
            and_(
                Dossier.cabinet_id == cabinet_id,
                Dossier.statut != StatusDossier.ARCHIVE,
                Echeance.date_echeance >= today,
                Echeance.date_echeance <= deadline,
                Echeance.statut != 'COMPLETE'
            )
        ).all()
        
        for echeance in echeances:
            dossier = echeance.dossier
            responsable = dossier.responsable or dossier.user
            
            # Vérifier si une notification a déjà été envoyée aujourd'hui
            existing_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == responsable.id,
                    Notification.sent_at >= datetime.now().replace(hour=0, minute=0, second=0),
                    Notification.message.contains(f"Échéance proche - {dossier.reference}")
                )
            ).first()
            
            if not existing_notification:
                days_remaining = (echeance.date_echeance - today).days
                
                # Créer une alerte
                alerte = Alerte(
                    cabinet_id=cabinet_id,
                    dossier_id=dossier.id,
                    type_alerte=TypeAlerte.DEADLINE_PROCHE,
                    niveau=NiveauAlerte.WARNING if days_remaining > 3 else NiveauAlerte.URGENT,
                    message=f"Échéance le {echeance.date_echeance.strftime('%d/%m/%Y')} - {days_remaining} jour(s) restant(s)"
                )
                db.add(alerte)
                db.flush()
                
                # Créer une notification
                notification = Notification(
                    cabinet_id=cabinet_id,
                    user_id=responsable.id,
                    alerte_id=alerte.id,
                    title=f"Échéance proche - {dossier.nom_client}",
                    message=f"Le dossier {dossier.reference} a une échéance le {echeance.date_echeance.strftime('%d/%m/%Y')}",
                    type_notification="email"
                )
                db.add(notification)
                
                # Envoyer l'email
                await email_service.send_notification_echeance(
                    to_email=responsable.email,
                    user_name=responsable.full_name or responsable.username,
                    dossier_reference=dossier.reference,
                    client_name=dossier.nom_client,
                    echeance_date=echeance.date_echeance.strftime('%d/%m/%Y'),
                    days_remaining=days_remaining
                )
        
        db.commit()
    
    @staticmethod
    async def _check_documents_manquants(db: Session, cabinet_id: int):
        """Vérifie les documents manquants pour les échéances en cours"""
        # Récupérer les dossiers actifs
        dossiers = db.query(Dossier).filter(
            and_(
                Dossier.cabinet_id == cabinet_id,
                Dossier.statut.in_([StatusDossier.EN_COURS, StatusDossier.NOUVEAU])
            )
        ).all()
        
        for dossier in dossiers:
            # Vérifier les documents requis non fournis
            documents_manquants = db.query(DocumentRequis).join(Echeance).filter(
                and_(
                    DocumentRequis.dossier_id == dossier.id,
                    DocumentRequis.est_applicable == True,
                    DocumentRequis.est_fourni == False,
                    Echeance.statut != 'COMPLETE'
                )
            ).all()
            
            if documents_manquants:
                responsable = dossier.responsable or dossier.user
                
                # Grouper par mois/année
                docs_par_periode = {}
                for doc in documents_manquants:
                    key = f"{doc.mois}-{doc.annee}"
                    if key not in docs_par_periode:
                        docs_par_periode[key] = []
                    docs_par_periode[key].append(doc.type_document.value)
                
                # Envoyer une notification par période
                for periode, types_docs in docs_par_periode.items():
                    mois, annee = periode.split('-')
                    mois_nom = [
                        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
                    ][int(mois) - 1]
                    
                    # Vérifier si une notification a déjà été envoyée cette semaine
                    existing_notification = db.query(Notification).filter(
                        and_(
                            Notification.user_id == responsable.id,
                            Notification.sent_at >= datetime.now() - timedelta(days=7),
                            Notification.message.contains(f"Documents manquants - {dossier.reference} - {mois_nom} {annee}")
                        )
                    ).first()
                    
                    if not existing_notification:
                        # Créer une alerte
                        alerte = Alerte(
                            cabinet_id=cabinet_id,
                            dossier_id=dossier.id,
                            type_alerte=TypeAlerte.DOCUMENT_MANQUANT,
                            niveau=NiveauAlerte.WARNING,
                            message=f"Documents manquants pour {mois_nom} {annee}: {', '.join(types_docs)}"
                        )
                        db.add(alerte)
                        db.flush()
                        
                        # Créer une notification
                        notification = Notification(
                            cabinet_id=cabinet_id,
                            user_id=responsable.id,
                            alerte_id=alerte.id,
                            title=f"Documents manquants - {dossier.nom_client}",
                            message=f"Documents manquants - {dossier.reference} - {mois_nom} {annee}",
                            type_notification="email"
                        )
                        db.add(notification)
                        
                        # Envoyer l'email
                        await email_service.send_document_manquant(
                            to_email=responsable.email,
                            user_name=responsable.full_name or responsable.username,
                            dossier_reference=dossier.reference,
                            client_name=dossier.nom_client,
                            documents_manquants=types_docs,
                            mois=mois_nom,
                            annee=int(annee)
                        )
        
        db.commit()
    
    @staticmethod
    async def _check_taches_retard(db: Session, cabinet_id: int):
        """Vérifie les tâches en retard"""
        today = date.today()
        
        # Récupérer les échéances en retard
        echeances_retard = db.query(Echeance).join(Dossier).filter(
            and_(
                Dossier.cabinet_id == cabinet_id,
                Dossier.statut != StatusDossier.ARCHIVE,
                Echeance.date_echeance < today,
                Echeance.statut != 'COMPLETE'
            )
        ).all()
        
        # Grouper par dossier
        dossiers_retard = {}
        for echeance in echeances_retard:
            dossier_id = echeance.dossier_id
            if dossier_id not in dossiers_retard:
                dossiers_retard[dossier_id] = []
            
            jours_retard = (today - echeance.date_echeance).days
            dossiers_retard[dossier_id].append({
                'nom': f"{echeance.periode_label}",
                'date_echeance': echeance.date_echeance.strftime('%d/%m/%Y'),
                'jours_retard': jours_retard
            })
        
        # Envoyer les notifications
        for dossier_id, taches in dossiers_retard.items():
            dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
            if not dossier:
                continue
            
            responsable = dossier.responsable or dossier.user
            
            # Vérifier si une notification a déjà été envoyée aujourd'hui
            existing_notification = db.query(Notification).filter(
                and_(
                    Notification.user_id == responsable.id,
                    Notification.sent_at >= datetime.now().replace(hour=0, minute=0, second=0),
                    Notification.message.contains(f"Tâches en retard - {dossier.reference}")
                )
            ).first()
            
            if not existing_notification:
                # Créer une alerte
                alerte = Alerte(
                    cabinet_id=cabinet_id,
                    dossier_id=dossier.id,
                    type_alerte=TypeAlerte.RETARD,
                    niveau=NiveauAlerte.URGENT,
                    message=f"{len(taches)} tâche(s) en retard"
                )
                db.add(alerte)
                db.flush()
                
                # Créer une notification
                notification = Notification(
                    cabinet_id=cabinet_id,
                    user_id=responsable.id,
                    alerte_id=alerte.id,
                    title=f"Tâches en retard - {dossier.nom_client}",
                    message=f"Tâches en retard - {dossier.reference}",
                    type_notification="email"
                )
                db.add(notification)
                
                # Envoyer l'email
                await email_service.send_tache_retard(
                    to_email=responsable.email,
                    user_name=responsable.full_name or responsable.username,
                    dossier_reference=dossier.reference,
                    client_name=dossier.nom_client,
                    taches_retard=taches
                )
        
        db.commit()
    
    @staticmethod
    async def send_welcome_notification(db: Session, user: User, temporary_password: str):
        """Envoie un email de bienvenue à un nouvel utilisateur"""
        try:
            # Créer une notification
            notification = Notification(
                cabinet_id=user.cabinet_id,
                user_id=user.id,
                title="Bienvenue sur Cabinet Comptable",
                message=f"Votre compte a été créé. Nom d'utilisateur: {user.username}",
                type_notification="email"
            )
            db.add(notification)
            db.commit()
            
            # Envoyer l'email
            await email_service.send_welcome_email(
                to_email=user.email,
                user_name=user.full_name or user.username,
                username=user.username,
                temporary_password=temporary_password
            )
            
            logger.info(f"Email de bienvenue envoyé à {user.email}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
    
    @staticmethod
    def mark_notification_read(db: Session, notification_id: int, user_id: int):
        """Marque une notification comme lue"""
        notification = db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now()
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_user_notifications(
        db: Session, 
        user_id: int, 
        cabinet_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Récupère les notifications d'un utilisateur"""
        query = db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.cabinet_id == cabinet_id
            )
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.sent_at.desc()).limit(limit).all()