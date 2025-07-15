from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.core.deps import get_current_cabinet_id
from app.models.user import User
from app.models.client import Client


class ClientCreate(BaseModel):
    nom: str
    numero_client: Optional[str] = None
    forme_juridique: str
    siret: Optional[str] = None
    nom_gerant: Optional[str] = None
    telephone_gerant: Optional[str] = None
    email_gerant: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    user_id: Optional[int] = None


class ClientUpdate(ClientCreate):
    pass


router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_clients(
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Liste les clients selon le rôle de l'utilisateur"""
    query = db.query(Client).filter(
        Client.is_active == True,
        Client.cabinet_id == cabinet_id
    )
    
    # RESTRICTION D'ACCÈS SELON LE RÔLE
    if current_user.role == "collaborateur":
        # Les collaborateurs ne voient que leurs clients assignés
        query = query.filter(Client.user_id == current_user.id)
    # Les managers et admins voient tous les clients
    
    clients = query.all()
    
    return [
        {
            "id": client.id,
            "nom": client.nom,
            "numero_client": client.numero_client,
            "forme_juridique": client.forme_juridique,
            "siret": client.siret,
            "email": client.email,
            "telephone": client.telephone,
            "nom_gerant": client.nom_gerant,
            "telephone_gerant": client.telephone_gerant,
            "email_gerant": client.email_gerant,
            "adresse": client.adresse,
            "ville": client.ville,
            "code_postal": client.code_postal,
            "user_id": client.user_id,
            "responsable": {
                "id": client.responsable.id,
                "username": client.responsable.username,
                "full_name": client.responsable.full_name
            } if client.responsable else None
        }
        for client in clients
    ]


@router.get("/{client_id}")
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Récupère un client par son ID"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.cabinet_id == cabinet_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return {
        "id": client.id,
        "nom": client.nom,
        "numero_client": client.numero_client,
        "forme_juridique": client.forme_juridique,
        "siret": client.siret,
        "email": client.email,
        "telephone": client.telephone,
        "nom_gerant": client.nom_gerant,
        "telephone_gerant": client.telephone_gerant,
        "email_gerant": client.email_gerant,
        "adresse": client.adresse,
        "ville": client.ville,
        "code_postal": client.code_postal,
        "user_id": client.user_id,
        "responsable": {
            "id": client.responsable.id,
            "username": client.responsable.username,
            "full_name": client.responsable.full_name
        } if client.responsable else None
    }


@router.post("/", response_model=dict)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Créer un nouveau client"""
    # Générer un numéro client si non fourni
    if not client_data.numero_client:
        count = db.query(Client).filter(Client.cabinet_id == cabinet_id).count()
        client_data.numero_client = f"CLI{str(count + 1).zfill(5)}"
    
    # Vérifier l'unicité du numéro client dans le cabinet
    existing = db.query(Client).filter(
        Client.numero_client == client_data.numero_client,
        Client.cabinet_id == cabinet_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro client existe déjà")
    
    client = Client(**client_data.dict(), cabinet_id=cabinet_id)
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return {
        "id": client.id,
        "nom": client.nom,
        "numero_client": client.numero_client,
        "forme_juridique": client.forme_juridique,
        "siret": client.siret,
        "email": client.email,
        "telephone": client.telephone,
        "message": "Client créé avec succès"
    }


@router.put("/{client_id}", response_model=dict)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Mettre à jour un client"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.cabinet_id == cabinet_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    for field, value in client_data.dict(exclude_unset=True).items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    return {
        "id": client.id,
        "nom": client.nom,
        "message": "Client mis à jour avec succès"
    }


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    cabinet_id: int = Depends(get_current_cabinet_id),
    db: Session = Depends(get_db)
):
    """Supprimer un client"""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.cabinet_id == cabinet_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Vérifier s'il a des dossiers
    from app.models.dossier import Dossier
    dossiers_count = db.query(Dossier).filter(Dossier.nom_client == client.nom).count()
    if dossiers_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Impossible de supprimer ce client car il a {dossiers_count} dossier(s) associé(s)"
        )
    
    db.delete(client)
    db.commit()
    
    return {"message": "Client supprimé avec succès"}