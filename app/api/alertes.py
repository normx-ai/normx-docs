from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.alerte import Alerte as AlerteModel, TypeAlerte, NiveauAlerte
from app.models.dossier import Dossier
from app.schemas.alerte import (
    Alerte, AlerteCreate, AlerteResolve, AlerteWithDossier,
    AlerteDashboard, TypeAlerteEnum, NiveauAlerteEnum
)
from app.services.alerte_service import AlerteService

router = APIRouter()


@router.get("/", response_model=List[AlerteWithDossier])
async def list_alertes(
    type_alerte: Optional[TypeAlerteEnum] = Query(None, description="Type d'alerte"),
    active: Optional[bool] = Query(True, description="Alertes actives uniquement"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AlerteModel).join(Dossier)
    
    if active is not None:
        query = query.filter(AlerteModel.active == active)
    if type_alerte:
        query = query.filter(AlerteModel.type_alerte == type_alerte)
    
    # Filtrer selon le rôle
    if current_user.role == "collaborateur":
        query = query.filter(Dossier.responsable_id == current_user.id)
    
    alertes = query.order_by(AlerteModel.niveau.desc(), AlerteModel.created_at.desc()).all()
    
    result = []
    for alerte in alertes:
        alerte_dict = alerte.__dict__
        alerte_dict['dossier_client_name'] = alerte.dossier.client_name
        alerte_dict['dossier_type'] = alerte.dossier.type_dossier.value
        alerte_dict['dossier_deadline'] = alerte.dossier.deadline
        result.append(AlerteWithDossier(**alerte_dict))
    
    return result


@router.post("/", response_model=Alerte)
async def create_alerte(
    alerte_data: AlerteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alerte_service = AlerteService(db)
    alerte = alerte_service.create_alerte(
        dossier_id=alerte_data.dossier_id,
        type_alerte=alerte_data.type_alerte,
        message=alerte_data.message,
        niveau=alerte_data.niveau
    )
    db.commit()
    return alerte


@router.get("/dashboard", response_model=AlerteDashboard)
async def get_alertes_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Récupérer les alertes actives
    query = db.query(AlerteModel).join(Dossier).filter(AlerteModel.active == True)
    
    if current_user.role == "collaborateur":
        query = query.filter(Dossier.responsable_id == current_user.id)
    
    alertes = query.all()
    
    # Catégoriser les alertes
    alertes_urgentes = []
    alertes_retard = []
    alertes_documents = []
    
    for alerte in alertes:
        alerte_dict = alerte.__dict__
        alerte_dict['dossier_client_name'] = alerte.dossier.client_name
        alerte_dict['dossier_type'] = alerte.dossier.type_dossier.value
        alerte_dict['dossier_deadline'] = alerte.dossier.deadline
        alerte_obj = AlerteWithDossier(**alerte_dict)
        
        if alerte.niveau == NiveauAlerte.URGENT:
            alertes_urgentes.append(alerte_obj)
        if alerte.type_alerte == TypeAlerte.RETARD:
            alertes_retard.append(alerte_obj)
        if alerte.type_alerte == TypeAlerte.DOCUMENT_MANQUANT:
            alertes_documents.append(alerte_obj)
    
    # Statistiques
    today = date.today()
    resolues_aujourdhui = db.query(AlerteModel).filter(
        and_(
            AlerteModel.resolved_at >= today,
            AlerteModel.resolved_at < today + timedelta(days=1)
        )
    ).count()
    
    return AlerteDashboard(
        alertes_urgentes=alertes_urgentes,
        alertes_retard=alertes_retard,
        alertes_documents_manquants=alertes_documents,
        statistiques={
            "total_actives": len(alertes),
            "urgentes": len(alertes_urgentes),
            "warnings": len([a for a in alertes if a.niveau == NiveauAlerte.WARNING]),
            "resolues_aujourdhui": resolues_aujourdhui
        }
    )


@router.put("/{alerte_id}/resolve", response_model=Alerte)
async def resolve_alerte(
    alerte_id: int,
    resolve_data: AlerteResolve,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    alerte_service = AlerteService(db)
    alerte = alerte_service.resolve_alerte(alerte_id, resolve_data.resolution_note)
    
    if not alerte:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    db.commit()
    return alerte


@router.post("/batch-check")
async def check_and_create_alertes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Seuls les admins peuvent déclencher cette vérification
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    
    # Déclencher la tâche Celery
    from app.workers.tasks import check_and_create_alerts
    task = check_and_create_alerts.delay()
    
    return {
        "task_id": task.id,
        "status": "Vérification lancée",
        "message": "La vérification des alertes a été déclenchée"
    }


@router.get("/notifications/unread")
async def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.services.notification_service import NotificationService
    notification_service = NotificationService(db)
    
    unread_count = notification_service.get_unread_count(current_user.id)
    notifications = notification_service.get_notifications_for_user(
        current_user.id, 
        unread_only=True
    )
    
    return {
        "count": unread_count,
        "notifications": notifications
    }