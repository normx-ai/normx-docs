"""
API des notifications
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_cabinet_id
from app.models.user import User
from app.models.notification import Notification
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationResponse, NotificationList

router = APIRouter()


@router.get("/", response_model=NotificationList)
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Récupérer les notifications de l'utilisateur courant"""
    notifications = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        cabinet_id=cabinet_id,
        unread_only=unread_only,
        limit=limit
    )
    
    # Compter les non lues
    unread_count = len([n for n in notifications if not n.is_read])
    
    return {
        "notifications": notifications,
        "unread_count": unread_count,
        "total": len(notifications)
    }


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marquer une notification comme lue"""
    success = NotificationService.mark_notification_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Notification non trouvée ou déjà lue"
        )
    
    return {"message": "Notification marquée comme lue"}


@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Marquer toutes les notifications comme lues"""
    # Récupérer toutes les notifications non lues
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.cabinet_id == cabinet_id,
        Notification.is_read == False
    ).all()
    
    count = 0
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.now()
        count += 1
    
    db.commit()
    
    return {
        "message": f"{count} notification(s) marquée(s) comme lue(s)",
        "count": count
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Obtenir le nombre de notifications non lues"""
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.cabinet_id == cabinet_id,
        Notification.is_read == False
    ).count()
    
    return {"unread_count": count}


@router.post("/test-email")
async def test_email_notification(
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Tester l'envoi d'un email de notification"""
    # Créer une notification de test
    from app.services.email_service import email_service
    
    try:
        # Envoyer un email de test
        success = await email_service.send_email(
            to_email=current_user.email,
            subject="Test de notification - Cabinet Comptable",
            template_name="test",
            template_data={
                "user_name": current_user.full_name or current_user.username,
                "message": "Ceci est un email de test pour vérifier que le système de notifications fonctionne correctement."
            }
        )
        
        if success:
            # Créer la notification en base
            notification = Notification(
                cabinet_id=cabinet_id,
                user_id=current_user.id,
                title="Email de test envoyé",
                message="Un email de test a été envoyé à votre adresse",
                type_notification="email"
            )
            db.add(notification)
            db.commit()
            
            return {"message": "Email de test envoyé avec succès"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Erreur lors de l'envoi de l'email"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'envoi de l'email: {str(e)}"
        )