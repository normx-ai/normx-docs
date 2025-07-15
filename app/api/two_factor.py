"""
Endpoints pour l'authentification à deux facteurs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.two_factor import TwoFactorAuth
from app.schemas.two_factor import (
    TwoFactorSetup, TwoFactorEnable, TwoFactorVerify,
    TwoFactorBackupCodes, TwoFactorStatus
)

router = APIRouter()
logger = logging.getLogger(__name__)
security_logger = logging.getLogger('security')


@router.get("/status", response_model=TwoFactorStatus)
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtenir le statut 2FA de l'utilisateur"""
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()
    
    return {
        "enabled": two_factor.enabled if two_factor else False,
        "activated_at": two_factor.activated_at if two_factor else None
    }


@router.post("/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialiser la configuration 2FA pour un utilisateur"""
    # Vérifier si 2FA existe déjà
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()
    
    if two_factor and two_factor.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'authentification à deux facteurs est déjà activée"
        )
    
    # Créer ou réinitialiser
    if not two_factor:
        two_factor = TwoFactorAuth(user_id=current_user.id)
        db.add(two_factor)
    
    # Générer un nouveau secret
    two_factor.generate_secret()
    
    # Générer les codes de récupération
    backup_codes = two_factor.generate_backup_codes()
    
    db.commit()
    
    # Log de sécurité
    security_logger.info(
        "2FA setup initiated",
        extra={
            'user_id': current_user.id,
            'username': current_user.username
        }
    )
    
    return {
        "secret": two_factor.secret,
        "qr_code": two_factor.generate_qr_code(current_user.email),
        "backup_codes": backup_codes
    }


@router.post("/enable")
async def enable_2fa(
    data: TwoFactorEnable,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activer 2FA après vérification du code"""
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()
    
    if not two_factor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Configuration 2FA non trouvée. Veuillez d'abord configurer 2FA."
        )
    
    if two_factor.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'authentification à deux facteurs est déjà activée"
        )
    
    # Vérifier le code
    if not two_factor.verify_token(data.token):
        security_logger.warning(
            "Failed 2FA activation attempt",
            extra={
                'user_id': current_user.id,
                'username': current_user.username
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide"
        )
    
    # Activer 2FA
    two_factor.enabled = True
    two_factor.activated_at = db.func.now()
    db.commit()
    
    # Log de sécurité
    security_logger.info(
        "2FA enabled successfully",
        extra={
            'user_id': current_user.id,
            'username': current_user.username
        }
    )
    
    return {"message": "Authentification à deux facteurs activée avec succès"}


@router.post("/disable")
async def disable_2fa(
    data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Désactiver 2FA"""
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()
    
    if not two_factor or not two_factor.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'authentification à deux facteurs n'est pas activée"
        )
    
    # Vérifier le code ou le code de récupération
    valid = False
    if len(data.token) == 6:
        # Code TOTP
        valid = two_factor.verify_token(data.token)
    else:
        # Code de récupération
        valid = two_factor.verify_backup_code(data.token)
    
    if not valid:
        security_logger.warning(
            "Failed 2FA disable attempt",
            extra={
                'user_id': current_user.id,
                'username': current_user.username
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide"
        )
    
    # Désactiver 2FA
    two_factor.enabled = False
    db.commit()
    
    # Log de sécurité
    security_logger.info(
        "2FA disabled",
        extra={
            'user_id': current_user.id,
            'username': current_user.username
        }
    )
    
    return {"message": "Authentification à deux facteurs désactivée"}


@router.post("/regenerate-backup-codes", response_model=TwoFactorBackupCodes)
async def regenerate_backup_codes(
    data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Régénérer les codes de récupération"""
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()
    
    if not two_factor or not two_factor.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'authentification à deux facteurs n'est pas activée"
        )
    
    # Vérifier le code TOTP
    if not two_factor.verify_token(data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide"
        )
    
    # Générer de nouveaux codes
    backup_codes = two_factor.generate_backup_codes()
    db.commit()
    
    # Log de sécurité
    security_logger.info(
        "Backup codes regenerated",
        extra={
            'user_id': current_user.id,
            'username': current_user.username
        }
    )
    
    return {"backup_codes": backup_codes}


@router.post("/verify")
async def verify_2fa_code(
    data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vérifier un code 2FA (pour test)"""
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == current_user.id
    ).first()
    
    if not two_factor or not two_factor.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'authentification à deux facteurs n'est pas activée"
        )
    
    # Vérifier le code
    valid = False
    if len(data.token) == 6:
        valid = two_factor.verify_token(data.token)
    else:
        valid = two_factor.verify_backup_code(data.token)
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide"
        )
    
    return {"message": "Code valide"}