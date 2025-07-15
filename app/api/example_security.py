"""
Exemple d'utilisation des fonctionnalités de sécurité dans les routes API
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.core.security import (
    limiter,
    validate_email,
    validate_password_strength,
    validate_phone,
    validate_siret,
    sanitize_string,
    require_strong_password
)
from app.core.deps import get_current_user
from app.models import User

router = APIRouter()


class UserRegistration(BaseModel):
    email: str = Field(..., description="Email de l'utilisateur")
    password: str = Field(..., description="Mot de passe")
    nom: str = Field(..., description="Nom de famille")
    prenom: str = Field(..., description="Prénom")
    telephone: Optional[str] = Field(None, description="Numéro de téléphone")
    siret: Optional[str] = Field(None, description="SIRET de l'entreprise")


class SecureMessage(BaseModel):
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=1000)
    recipient_email: str


@router.post("/register-secure")
@limiter.limit("5/hour")  # Limite à 5 inscriptions par heure par IP
async def register_with_validation(
    request: Request,
    user_data: UserRegistration
):
    """
    Inscription sécurisée avec validation complète des données
    """
    # Valider l'email
    if not validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="Format d'email invalide")
    
    # Valider le mot de passe
    valid, message = validate_password_strength(user_data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=message)
    
    # Valider le téléphone si fourni
    if user_data.telephone and not validate_phone(user_data.telephone):
        raise HTTPException(status_code=400, detail="Format de téléphone invalide")
    
    # Valider le SIRET si fourni
    if user_data.siret and not validate_siret(user_data.siret):
        raise HTTPException(status_code=400, detail="SIRET invalide")
    
    # Nettoyer les chaînes
    nom = sanitize_string(user_data.nom, max_length=50)
    prenom = sanitize_string(user_data.prenom, max_length=50)
    
    return {
        "message": "Données validées avec succès",
        "data": {
            "email": user_data.email,
            "nom": nom,
            "prenom": prenom,
            "telephone": user_data.telephone,
            "siret": user_data.siret
        }
    }


@router.post("/send-message")
@limiter.limit("20/minute")  # 20 messages par minute maximum
async def send_secure_message(
    request: Request,
    message: SecureMessage,
    current_user: User = Depends(get_current_user)
):
    """
    Envoyer un message sécurisé avec validation et nettoyage
    """
    # Valider l'email du destinataire
    if not validate_email(message.recipient_email):
        raise HTTPException(status_code=400, detail="Email du destinataire invalide")
    
    # Nettoyer le contenu
    title = sanitize_string(message.title, max_length=100)
    content = sanitize_string(message.content, max_length=1000)
    
    # Ici on enverrait le message...
    
    return {
        "message": "Message envoyé avec succès",
        "title": title,
        "recipient": message.recipient_email,
        "sender": current_user.email
    }


@router.get("/public-info")
@limiter.limit("100/minute")  # Limite généreuse pour les endpoints publics
async def get_public_info(request: Request):
    """
    Endpoint public avec rate limiting
    """
    return {
        "message": "Information publique",
        "rate_limit": "100 requêtes par minute"
    }


@router.get("/sensitive-data")
@limiter.limit("10/hour")  # Limite stricte pour les données sensibles
async def get_sensitive_data(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint pour données sensibles avec rate limiting strict
    """
    return {
        "message": "Données sensibles",
        "user": current_user.email,
        "rate_limit": "10 requêtes par heure"
    }


# Exemple avec rate limiting personnalisé par utilisateur
@router.get("/user-specific")
@limiter.limit("50/hour", key_func=lambda request: request.state.user.email if hasattr(request.state, 'user') else get_remote_address(request))
async def user_specific_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Rate limiting basé sur l'utilisateur plutôt que l'IP
    """
    # Stocker l'utilisateur dans request.state pour le key_func
    request.state.user = current_user
    
    return {
        "message": f"Endpoint spécifique pour {current_user.email}",
        "rate_limit": "50 requêtes par heure par utilisateur"
    }