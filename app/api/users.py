from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.core.deps import get_current_cabinet_id
from app.core.security import get_password_hash
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate, CabinetSettings, UserCreate

router = APIRouter()


@router.get("/me", response_model=User)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=List[User])
async def list_users(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):
    # Seuls les admins et managers peuvent voir tous les utilisateurs
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Permissions insuffisantes"
        )
    
    # Filtrer par cabinet
    users = db.query(UserModel).filter(UserModel.cabinet_id == cabinet_id).all()
    return users


@router.put("/me", response_model=User)
async def update_me(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Mettre à jour les champs fournis
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    # Seuls les admins peuvent changer les rôles
    if user_update.role is not None and current_user.role == "admin":
        current_user.role = user_update.role
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put("/cabinet-settings", response_model=User)
async def update_cabinet_settings(
    settings: CabinetSettings,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):
    """Mettre à jour les paramètres du cabinet"""
    # Mettre à jour les champs fournis
    if settings.cabinet_name is not None:
        current_user.cabinet_name = settings.cabinet_name
    if settings.siret is not None:
        current_user.siret = settings.siret
    if settings.siren is not None:
        current_user.siren = settings.siren
    if settings.nom_gerant is not None:
        current_user.nom_gerant = settings.nom_gerant
    if settings.adresse_cabinet is not None:
        current_user.adresse_cabinet = settings.adresse_cabinet
    if settings.code_postal is not None:
        current_user.code_postal = settings.code_postal
    if settings.ville is not None:
        current_user.ville = settings.ville
    if settings.telephone_cabinet is not None:
        current_user.telephone_cabinet = settings.telephone_cabinet
    if settings.email_cabinet is not None:
        current_user.email_cabinet = settings.email_cabinet
    if settings.site_web is not None:
        current_user.site_web = settings.site_web
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/all", response_model=List[User])
async def get_all_users(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtenir tous les utilisateurs (admin/manager uniquement)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Permissions insuffisantes"
        )
    
    users = db.query(UserModel).all()
    return users


@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    cabinet_id: int = Depends(get_current_cabinet_id)
):
    """Créer un nouvel utilisateur (admin uniquement)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs peuvent créer des utilisateurs"
        )
    
    # Vérifier si l'utilisateur existe déjà dans ce cabinet
    existing_user = db.query(UserModel).filter(
        UserModel.username == user_data.username,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Ce nom d'utilisateur existe déjà dans ce cabinet"
        )
    
    # Créer le nouvel utilisateur
    hashed_password = get_password_hash(user_data.password)
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        cabinet_id=cabinet_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Modifier un utilisateur (admin/manager uniquement)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=403,
            detail="Permissions insuffisantes"
        )
    
    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Les managers ne peuvent pas modifier les admins
    if current_user.role == "manager" and user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Un manager ne peut pas modifier un administrateur"
        )
    
    # Mettre à jour les champs
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None and current_user.role == "admin":
        user.role = user_update.role
    
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activer/désactiver un utilisateur (admin uniquement)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs peuvent modifier le statut des utilisateurs"
        )
    
    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Ne pas permettre de désactiver son propre compte
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"Utilisateur {'activé' if user.is_active else 'désactivé'} avec succès"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprimer un utilisateur (admin uniquement)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Seuls les administrateurs peuvent supprimer des utilisateurs"
        )
    
    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.cabinet_id == cabinet_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Ne pas permettre de supprimer son propre compte
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "Utilisateur supprimé avec succès"}