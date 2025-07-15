from datetime import datetime, timedelta, date
from typing import List
import logging

from celery import shared_task
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.dossier import Dossier, StatusDossier
from app.models.alerte import Alerte, TypeAlerte, NiveauAlerte
from app.models.notification import Notification
from app.models.user import User
from app.services.notification_service import NotificationService
from app.services.alerte_service import AlerteService

logger = logging.getLogger(__name__)


@shared_task(name="app.workers.tasks.check_and_create_alerts")
def check_and_create_alerts():
    """Vérifier tous les dossiers et créer des alertes automatiques"""
    db = SessionLocal()
    alerte_service = AlerteService(db)
    
    try:
        # Compter les alertes créées
        alerts_created = {
            "retard": 0,
            "deadline_proche": 0,
            "documents_manquants": 0,
            "inactivite": 0
        }
        
        # Récupérer tous les dossiers actifs
        dossiers = db.query(Dossier).filter(
            Dossier.status.in_([StatusDossier.EN_COURS, StatusDossier.EN_ATTENTE])
        ).all()
        
        for dossier in dossiers:
            # Vérifier les retards
            if dossier.deadline < date.today() and dossier.status != StatusDossier.COMPLETE:
                if alerte_service.create_alerte_retard(dossier):
                    alerts_created["retard"] += 1
            
            # Vérifier les deadlines proches (3 jours)
            elif dossier.deadline <= date.today() + timedelta(days=3):
                if alerte_service.create_alerte_deadline_proche(dossier):
                    alerts_created["deadline_proche"] += 1
            
            # Vérifier l'inactivité (pas de mise à jour depuis 7 jours)
            if dossier.updated_at and dossier.updated_at < datetime.now() - timedelta(days=7):
                if alerte_service.create_alerte_inactivite(dossier):
                    alerts_created["inactivite"] += 1
        
        db.commit()
        
        logger.info(f"Alertes créées: {alerts_created}")
        return {
            "status": "success",
            "dossiers_verifies": len(dossiers),
            "alertes_creees": alerts_created,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la création des alertes: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        db.close()


@shared_task(name="app.workers.tasks.generate_daily_point")
def generate_daily_point():
    """Générer le point quotidien et l'envoyer aux managers"""
    db = SessionLocal()
    notification_service = NotificationService(db)
    
    try:
        # Statistiques du jour
        today = date.today()
        
        # Dossiers en retard
        dossiers_retard = db.query(Dossier).filter(
            and_(
                Dossier.deadline < today,
                Dossier.status != StatusDossier.COMPLETE
            )
        ).all()
        
        # Dossiers à traiter aujourd'hui
        dossiers_aujourdhui = db.query(Dossier).filter(
            and_(
                Dossier.deadline == today,
                Dossier.status != StatusDossier.COMPLETE
            )
        ).all()
        
        # Dossiers complétés hier
        yesterday = today - timedelta(days=1)
        dossiers_completes_hier = db.query(Dossier).filter(
            and_(
                Dossier.completed_at >= yesterday,
                Dossier.completed_at < today
            )
        ).all()
        
        # Créer le message du point quotidien
        message = f"""
📊 POINT QUOTIDIEN - {today.strftime('%d/%m/%Y')}

🚨 Dossiers en retard: {len(dossiers_retard)}
📅 Dossiers à traiter aujourd'hui: {len(dossiers_aujourdhui)}
✅ Dossiers complétés hier: {len(dossiers_completes_hier)}

Détails des urgences:
"""
        
        for dossier in dossiers_retard[:5]:  # Top 5 des retards
            jours_retard = (today - dossier.deadline).days
            message += f"\n• {dossier.client_name} - {dossier.type_dossier.value} - {jours_retard}j de retard"
        
        # Envoyer aux managers
        managers = db.query(User).filter(
            User.role.in_(["admin", "manager"])
        ).all()
        
        for manager in managers:
            notification_service.create_notification(
                user_id=manager.id,
                title="Point Quotidien",
                message=message,
                type_notification="email"
            )
        
        db.commit()
        
        logger.info("Point quotidien généré et envoyé")
        return {
            "status": "success",
            "recipients": len(managers),
            "stats": {
                "retard": len(dossiers_retard),
                "aujourdhui": len(dossiers_aujourdhui),
                "completes_hier": len(dossiers_completes_hier)
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la génération du point quotidien: {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@shared_task(name="app.workers.tasks.send_urgent_reminders")
def send_urgent_reminders():
    """Envoyer des rappels pour les dossiers urgents"""
    db = SessionLocal()
    notification_service = NotificationService(db)
    
    try:
        # Récupérer les alertes urgentes actives
        alertes_urgentes = db.query(Alerte).filter(
            and_(
                Alerte.active == True,
                Alerte.niveau == NiveauAlerte.URGENT
            )
        ).all()
        
        notifications_sent = 0
        
        for alerte in alertes_urgentes:
            if alerte.dossier and alerte.dossier.responsable:
                notification_service.create_notification(
                    user_id=alerte.dossier.responsable_id,
                    title=f"🚨 Rappel Urgent - {alerte.dossier.client_name}",
                    message=alerte.message,
                    type_notification="in_app",
                    alerte_id=alerte.id
                )
                notifications_sent += 1
        
        db.commit()
        
        logger.info(f"Rappels urgents envoyés: {notifications_sent}")
        return {
            "status": "success",
            "notifications_sent": notifications_sent
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de l'envoi des rappels: {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@shared_task(name="app.workers.tasks.cleanup_old_notifications")
def cleanup_old_notifications():
    """Nettoyer les anciennes notifications lues"""
    db = SessionLocal()
    
    try:
        # Supprimer les notifications lues de plus de 30 jours
        cutoff_date = datetime.now() - timedelta(days=30)
        
        deleted_count = db.query(Notification).filter(
            and_(
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            )
        ).delete()
        
        db.commit()
        
        logger.info(f"Notifications supprimées: {deleted_count}")
        return {
            "status": "success",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors du nettoyage: {str(e)}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@shared_task(name="app.workers.tasks.process_document")
def process_document(document_id: int):
    """Traiter un document avec l'IA (OCR, extraction de données)"""
    # TODO: Implémenter le traitement IA des documents
    logger.info(f"Traitement du document {document_id}")
    return {"status": "pending", "document_id": document_id}