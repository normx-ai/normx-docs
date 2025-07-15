from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date, timedelta
import asyncio

from app.core.database import SessionLocal
from app.models.dossier import Dossier, StatusDossier, PrioriteDossier
from app.models.user import User
from app.core.websocket import manager


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@shared_task
def check_deadlines():
    """Vérifier les échéances et envoyer des rappels"""
    db = SessionLocal()
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        # Dossiers avec échéance demain
        dossiers_tomorrow = db.query(Dossier).filter(
            and_(
                Dossier.date_echeance == tomorrow,
                Dossier.statut != StatusDossier.COMPLETE,
                Dossier.statut != StatusDossier.ARCHIVE
            )
        ).all()
        
        for dossier in dossiers_tomorrow:
            # Créer une notification
            reminder_data = {
                "dossier_id": dossier.id,
                "nom_client": dossier.nom_client,
                "type_dossier": dossier.type_dossier,
                "date_echeance": dossier.date_echeance.isoformat(),
                "message": f"Rappel : Le dossier {dossier.nom_client} arrive à échéance demain",
                "urgence": "haute"
            }
            
            # Envoyer via WebSocket
            asyncio.create_task(
                manager.notify_deadline_reminder(dossier.user_id, reminder_data)
            )
        
        # Dossiers avec échéance dans une semaine
        dossiers_next_week = db.query(Dossier).filter(
            and_(
                Dossier.date_echeance == next_week,
                Dossier.statut != StatusDossier.COMPLETE,
                Dossier.statut != StatusDossier.ARCHIVE
            )
        ).all()
        
        for dossier in dossiers_next_week:
            reminder_data = {
                "dossier_id": dossier.id,
                "nom_client": dossier.nom_client,
                "type_dossier": dossier.type_dossier,
                "date_echeance": dossier.date_echeance.isoformat(),
                "message": f"Rappel : Le dossier {dossier.nom_client} arrive à échéance dans 7 jours",
                "urgence": "moyenne"
            }
            
            asyncio.create_task(
                manager.notify_deadline_reminder(dossier.user_id, reminder_data)
            )
            
        return {
            "tomorrow": len(dossiers_tomorrow),
            "next_week": len(dossiers_next_week)
        }
        
    finally:
        db.close()


@shared_task
def check_urgent_dossiers():
    """Vérifier les dossiers urgents"""
    db = SessionLocal()
    try:
        # Dossiers marqués comme urgents
        dossiers_urgents = db.query(Dossier).filter(
            and_(
                Dossier.priorite == PrioriteDossier.URGENTE,
                Dossier.statut != StatusDossier.COMPLETE,
                Dossier.statut != StatusDossier.ARCHIVE
            )
        ).all()
        
        for dossier in dossiers_urgents:
            alert_data = {
                "dossier_id": dossier.id,
                "nom_client": dossier.nom_client,
                "type_dossier": dossier.type_dossier,
                "message": f"Dossier urgent : {dossier.nom_client} nécessite votre attention",
                "niveau": "urgent"
            }
            
            asyncio.create_task(
                manager.notify_new_alert(dossier.user_id, alert_data)
            )
            
        return {"urgent_count": len(dossiers_urgents)}
        
    finally:
        db.close()


@shared_task
def check_overdue_dossiers():
    """Vérifier les dossiers en retard"""
    db = SessionLocal()
    try:
        today = date.today()
        
        # Dossiers nouvellement en retard (échéance = hier)
        yesterday = today - timedelta(days=1)
        new_overdue = db.query(Dossier).filter(
            and_(
                Dossier.date_echeance == yesterday,
                Dossier.statut != StatusDossier.COMPLETE,
                Dossier.statut != StatusDossier.ARCHIVE
            )
        ).all()
        
        for dossier in new_overdue:
            alert_data = {
                "dossier_id": dossier.id,
                "nom_client": dossier.nom_client,
                "type_dossier": dossier.type_dossier,
                "date_echeance": dossier.date_echeance.isoformat(),
                "message": f"Attention : Le dossier {dossier.nom_client} est maintenant en retard",
                "niveau": "urgent"
            }
            
            asyncio.create_task(
                manager.notify_new_alert(dossier.user_id, alert_data)
            )
            
        # Dossiers en retard depuis plus de 3 jours
        critical_date = today - timedelta(days=3)
        critical_overdue = db.query(Dossier).filter(
            and_(
                Dossier.date_echeance == critical_date,
                Dossier.statut != StatusDossier.COMPLETE,
                Dossier.statut != StatusDossier.ARCHIVE
            )
        ).all()
        
        for dossier in critical_overdue:
            alert_data = {
                "dossier_id": dossier.id,
                "nom_client": dossier.nom_client,
                "type_dossier": dossier.type_dossier,
                "date_echeance": dossier.date_echeance.isoformat(),
                "message": f"CRITIQUE : Le dossier {dossier.nom_client} est en retard de 3 jours",
                "niveau": "critique"
            }
            
            asyncio.create_task(
                manager.notify_new_alert(dossier.user_id, alert_data)
            )
            
        return {
            "new_overdue": len(new_overdue),
            "critical_overdue": len(critical_overdue)
        }
        
    finally:
        db.close()


@shared_task
def send_daily_report():
    """Envoyer un rapport quotidien à chaque utilisateur"""
    db = SessionLocal()
    try:
        today = date.today()
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            # Statistiques pour cet utilisateur
            en_retard = db.query(Dossier).filter(
                and_(
                    Dossier.user_id == user.id,
                    Dossier.date_echeance < today,
                    Dossier.statut != StatusDossier.COMPLETE,
                    Dossier.statut != StatusDossier.ARCHIVE
                )
            ).count()
            
            aujourdhui = db.query(Dossier).filter(
                and_(
                    Dossier.user_id == user.id,
                    Dossier.date_echeance == today,
                    Dossier.statut != StatusDossier.COMPLETE,
                    Dossier.statut != StatusDossier.ARCHIVE
                )
            ).count()
            
            urgents = db.query(Dossier).filter(
                and_(
                    Dossier.user_id == user.id,
                    Dossier.priorite == PrioriteDossier.URGENTE,
                    Dossier.statut != StatusDossier.COMPLETE,
                    Dossier.statut != StatusDossier.ARCHIVE
                )
            ).count()
            
            report_data = {
                "type": "daily_report",
                "stats": {
                    "en_retard": en_retard,
                    "aujourdhui": aujourdhui,
                    "urgents": urgents
                },
                "message": f"Rapport quotidien : {en_retard} dossiers en retard, {aujourdhui} à traiter aujourd'hui, {urgents} urgents",
                "date": today.isoformat()
            }
            
            asyncio.create_task(
                manager.notify_deadline_reminder(user.id, report_data)
            )
            
        return {"users_notified": len(users)}
        
    finally:
        db.close()