from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.echeance import Echeance
from app.models.dossier import Dossier
from app.schemas.echeance import Echeance as EcheanceSchema, EcheanceUpdate

router = APIRouter()


@router.get("/dossiers/{dossier_id}/echeances", response_model=List[EcheanceSchema])
async def get_dossier_echeances(
    dossier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupérer toutes les échéances d'un dossier"""
    # Vérifier que le dossier existe et que l'utilisateur y a accès
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
    
    # Vérifier les permissions
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Récupérer les échéances
    echeances = db.query(Echeance).filter(
        Echeance.dossier_id == dossier_id
    ).order_by(Echeance.mois).all()
    
    return echeances


@router.put("/{echeance_id}", response_model=EcheanceSchema)
async def update_echeance(
    echeance_id: int,
    echeance_update: EcheanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour une échéance"""
    echeance = db.query(Echeance).filter(Echeance.id == echeance_id).first()
    if not echeance:
        raise HTTPException(status_code=404, detail="Échéance non trouvée")
    
    # Vérifier l'accès via le dossier
    dossier = echeance.dossier
    if current_user.role == "collaborateur":
        from app.models.client import Client
        clients_assignes = db.query(Client).filter(Client.user_id == current_user.id).all()
        noms_clients = [client.nom for client in clients_assignes]
        
        if dossier.nom_client not in noms_clients:
            raise HTTPException(status_code=403, detail="Accès refusé")
    
    # Mettre à jour les champs
    update_data = echeance_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(echeance, field, value)
    
    # Gérer les dates automatiques
    from datetime import datetime
    if echeance_update.statut == "COMPLETE" and not echeance.date_completion:
        echeance.date_completion = datetime.utcnow()
    elif echeance_update.statut != "COMPLETE":
        echeance.date_completion = None
    
    echeance.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(echeance)
    
    return echeance