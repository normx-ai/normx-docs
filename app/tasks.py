"""
Tâches asynchrones Celery
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.cabinet import Cabinet
from app.models.user import User
from app.models.dossier import Dossier, StatusDossier
from app.models.echeance import Echeance
from app.models.notification import Notification
from app.models.alerte import Alerte
from app.services.notification_service import NotificationService
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

# Créer une session pour les tâches
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(name="app.tasks.check_all_notifications")
def check_all_notifications():
    """
    Vérifie et envoie les notifications pour tous les cabinets actifs
    """
    db = SessionLocal()
    try:
        # Récupérer tous les cabinets actifs
        cabinets = db.query(Cabinet).filter(Cabinet.is_active == True).all()
        
        for cabinet in cabinets:
            logger.info(f"Vérification des notifications pour le cabinet {cabinet.nom}")
            
            # Appeler la fonction asynchrone de manière synchrone
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                NotificationService.check_and_send_notifications(db, cabinet.id)
            )
            
        logger.info(f"Vérification terminée pour {len(cabinets)} cabinet(s)")
        return {"status": "success", "cabinets_checked": len(cabinets)}
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des notifications: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.send_notification_email")
def send_notification_email(
    to_email: str,
    subject: str,
    template_name: str,
    template_data: Dict[str, Any]
):
    """
    Envoie un email de notification
    """
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            email_service.send_email(
                to_email=to_email,
                subject=subject,
                template_name=template_name,
                template_data=template_data
            )
        )
        
        if success:
            logger.info(f"Email envoyé avec succès à {to_email}")
            return {"status": "success", "email": to_email}
        else:
            logger.error(f"Échec de l'envoi de l'email à {to_email}")
            return {"status": "error", "email": to_email}
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.send_weekly_summary")
def send_weekly_summary():
    """
    Envoie un résumé hebdomadaire à tous les utilisateurs actifs
    """
    db = SessionLocal()
    try:
        # Pour chaque cabinet actif
        cabinets = db.query(Cabinet).filter(Cabinet.is_active == True).all()
        
        for cabinet in cabinets:
            # Récupérer les utilisateurs actifs du cabinet
            users = db.query(User).filter(
                User.cabinet_id == cabinet.id,
                User.is_active == True
            ).all()
            
            for user in users:
                # Calculer les statistiques de la semaine
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                
                # Dossiers en retard
                dossiers_retard = db.query(Dossier).join(Echeance).filter(
                    Dossier.cabinet_id == cabinet.id,
                    Dossier.responsable_id == user.id,
                    Echeance.date_echeance < today,
                    Echeance.statut != 'COMPLETE'
                ).count()
                
                # Échéances cette semaine
                echeances_semaine = db.query(Echeance).join(Dossier).filter(
                    Dossier.cabinet_id == cabinet.id,
                    Dossier.responsable_id == user.id,
                    Echeance.date_echeance >= today,
                    Echeance.date_echeance < today + timedelta(days=7),
                    Echeance.statut != 'COMPLETE'
                ).count()
                
                # Envoyer l'email si nécessaire
                if dossiers_retard > 0 or echeances_semaine > 0:
                    # TODO: Créer un template pour le résumé hebdomadaire
                    logger.info(f"Résumé hebdomadaire pour {user.email}: {dossiers_retard} en retard, {echeances_semaine} cette semaine")
        
        return {"status": "success", "cabinets_processed": len(cabinets)}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du résumé hebdomadaire: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.cleanup_old_notifications")
def cleanup_old_notifications():
    """
    Nettoie les anciennes notifications (plus de 90 jours)
    """
    db = SessionLocal()
    try:
        cutoff_date = datetime.now() - timedelta(days=90)
        
        # Supprimer les notifications lues de plus de 90 jours
        deleted_count = db.query(Notification).filter(
            Notification.is_read == True,
            Notification.sent_at < cutoff_date
        ).delete()
        
        # Supprimer les alertes résolues de plus de 90 jours
        deleted_alertes = db.query(Alerte).filter(
            Alerte.active == False,
            Alerte.resolved_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Nettoyage terminé: {deleted_count} notifications et {deleted_alertes} alertes supprimées")
        return {
            "status": "success",
            "notifications_deleted": deleted_count,
            "alertes_deleted": deleted_alertes
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.update_echeances_status")
def update_echeances_status():
    """
    Met à jour le statut des échéances (EN_RETARD si date dépassée)
    """
    db = SessionLocal()
    try:
        today = date.today()
        
        # Mettre à jour les échéances en retard
        updated_count = db.query(Echeance).filter(
            Echeance.date_echeance < today,
            Echeance.statut == 'A_FAIRE'
        ).update({
            'statut': 'EN_RETARD'
        })
        
        # Mettre à jour le statut des dossiers si nécessaire
        # Un dossier passe EN_ATTENTE s'il n'a pas d'activité depuis 7 jours
        week_ago = datetime.now() - timedelta(days=7)
        
        dossiers_inactifs = db.query(Dossier).filter(
            Dossier.statut == StatusDossier.EN_COURS,
            Dossier.updated_at < week_ago
        ).all()
        
        for dossier in dossiers_inactifs:
            if dossier.peut_passer_en_attente():
                dossier.statut = StatusDossier.EN_ATTENTE
        
        db.commit()
        
        logger.info(f"Mise à jour terminée: {updated_count} échéances en retard, {len(dossiers_inactifs)} dossiers en attente")
        return {
            "status": "success",
            "echeances_updated": updated_count,
            "dossiers_updated": len(dossiers_inactifs)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la mise à jour des statuts: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.send_welcome_email")
def send_welcome_email(user_id: int, temporary_password: str):
    """
    Envoie un email de bienvenue à un nouvel utilisateur
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "Utilisateur non trouvé"}
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(
            NotificationService.send_welcome_notification(db, user, temporary_password)
        )
        
        return {"status": "success", "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()