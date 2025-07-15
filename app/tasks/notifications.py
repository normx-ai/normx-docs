from celery import shared_task
import asyncio
from app.core.websocket import manager


@shared_task
def notify_dossier_created(user_id: int, dossier_data: dict):
    """Notifier la création d'un nouveau dossier"""
    notification_data = {
        "dossier_id": dossier_data.get("id"),
        "nom_client": dossier_data.get("nom_client"),
        "type_dossier": dossier_data.get("type_dossier"),
        "message": f"Nouveau dossier créé : {dossier_data.get('nom_client')}"
    }
    
    asyncio.create_task(
        manager.notify_dossier_update(user_id, notification_data)
    )
    
    return {"notified": True}


@shared_task
def notify_dossier_updated(user_id: int, dossier_data: dict, changes: dict):
    """Notifier la modification d'un dossier"""
    change_summary = []
    if "statut" in changes:
        change_summary.append(f"Statut: {changes['statut']['old']} → {changes['statut']['new']}")
    if "priorite" in changes:
        change_summary.append(f"Priorité: {changes['priorite']['old']} → {changes['priorite']['new']}")
    if "date_echeance" in changes:
        change_summary.append(f"Échéance modifiée")
    
    notification_data = {
        "dossier_id": dossier_data.get("id"),
        "nom_client": dossier_data.get("nom_client"),
        "type_dossier": dossier_data.get("type_dossier"),
        "message": f"Dossier modifié : {dossier_data.get('nom_client')}",
        "changes": ", ".join(change_summary)
    }
    
    asyncio.create_task(
        manager.notify_dossier_update(user_id, notification_data)
    )
    
    return {"notified": True}


@shared_task
def notify_dossier_completed(user_id: int, dossier_data: dict):
    """Notifier la complétion d'un dossier"""
    notification_data = {
        "dossier_id": dossier_data.get("id"),
        "nom_client": dossier_data.get("nom_client"),
        "type_dossier": dossier_data.get("type_dossier"),
        "message": f"Dossier complété : {dossier_data.get('nom_client')} ✓"
    }
    
    asyncio.create_task(
        manager.notify_dossier_update(user_id, notification_data)
    )
    
    return {"notified": True}