from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt
from typing import Optional
import hashlib
import secrets

from app.core.database import get_db
from app.core.security import (
    create_access_token, verify_password, verify_token,
    validate_password_strength, validate_email, validate_phone,
    validate_siret, sanitize_string, get_password_hash,
    create_refresh_token, verify_refresh_token, revoke_refresh_token,
    revoke_all_user_tokens
)
from app.core.validators import get_country_info, COUNTRY_CONFIGS
from app.core.config import settings
from app.models.user import User
from app.models.cabinet import Cabinet
from app.schemas.user import UserCreate, User as UserSchema, Token, TokenRefresh
from sqlalchemy import func
import re
import logging

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        username = verify_token(token, credentials_exception)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log de sécurité pour tentative échouée
        security_logger = logging.getLogger('security')
        security_logger.warning(
            "Failed login attempt",
            extra={
                'username': form_data.username,
                'ip_address': request.client.host if request.client else 'unknown'
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier si 2FA est activé
    from app.models.two_factor import TwoFactorAuth
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == user.id,
        TwoFactorAuth.enabled == True
    ).first()
    
    if two_factor:
        # Créer un token de session temporaire
        session_token = secrets.token_urlsafe(32)
        
        # Stocker temporairement dans Redis (5 minutes)
        from app.core.cache import redis_client
        redis_client.setex(
            f"2fa_session:{session_token}",
            300,  # 5 minutes
            str(user.id)
        )
        
        # Retourner un challenge 2FA
        return {
            "requires_2fa": True,
            "session_token": session_token,
            "message": "Veuillez entrer votre code d'authentification"
        }
    
    # Créer un identifiant de device basé sur l'IP et le user agent
    device_id = hashlib.sha256(
        f"{request.client.host if request.client else 'unknown'}:{request.headers.get('user-agent', '')}".encode()
    ).hexdigest()[:16]
    
    # Créer les tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "cabinet_id": user.cabinet_id}, expires_delta=access_token_expires
    )
    
    refresh_token, refresh_expires = create_refresh_token(
        user_id=user.id,
        db=db,
        device_id=device_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )
    
    # Log de succès
    security_logger = logging.getLogger('security')
    security_logger.info(
        "Successful login",
        extra={
            'user_id': user.id,
            'username': user.username,
            'ip_address': request.client.host if request.client else 'unknown'
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Rafraîchir l'access token avec un refresh token valide"""
    # Vérifier le refresh token
    user_id = verify_refresh_token(token_data.refresh_token, db)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré"
        )
    
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé ou inactif"
        )
    
    # Créer un nouveau access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "cabinet_id": user.cabinet_id}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/verify-2fa", response_model=Token)
async def verify_2fa_login(
    request: Request,
    data: dict,  # {"session_token": str, "code": str}
    db: Session = Depends(get_db)
):
    """Vérifier le code 2FA après le login"""
    from app.models.two_factor import TwoFactorAuth
    from app.core.cache import redis_client
    
    session_token = data.get("session_token")
    code = data.get("code")
    
    if not session_token or not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de session et code requis"
        )
    
    # Récupérer l'ID utilisateur depuis Redis
    user_id = redis_client.get(f"2fa_session:{session_token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée ou invalide"
        )
    
    # Supprimer la session temporaire
    redis_client.delete(f"2fa_session:{session_token}")
    
    # Récupérer l'utilisateur
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé"
        )
    
    # Vérifier le 2FA
    two_factor = db.query(TwoFactorAuth).filter(
        TwoFactorAuth.user_id == user.id
    ).first()
    
    if not two_factor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA non configuré"
        )
    
    # Vérifier le code
    valid = False
    if len(code) == 6:
        valid = two_factor.verify_token(code)
    else:
        valid = two_factor.verify_backup_code(code)
        if valid:
            db.commit()  # Sauvegarder la consommation du code de récupération
    
    if not valid:
        security_logger = logging.getLogger('security')
        security_logger.warning(
            "Failed 2FA verification",
            extra={
                'user_id': user.id,
                'username': user.username,
                'ip_address': request.client.host if request.client else 'unknown'
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Code invalide"
        )
    
    # Créer les tokens
    device_id = hashlib.sha256(
        f"{request.client.host if request.client else 'unknown'}:{request.headers.get('user-agent', '')}".encode()
    ).hexdigest()[:16]
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "cabinet_id": user.cabinet_id}, 
        expires_delta=access_token_expires
    )
    
    refresh_token, refresh_expires = create_refresh_token(
        user_id=user.id,
        db=db,
        device_id=device_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )
    
    # Log de succès
    security_logger = logging.getLogger('security')
    security_logger.info(
        "Successful 2FA login",
        extra={
            'user_id': user.id,
            'username': user.username,
            'ip_address': request.client.host if request.client else 'unknown'
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Déconnexion - révoque le refresh token"""
    if refresh_token:
        revoke_refresh_token(refresh_token, db)
    
    return {"message": "Déconnexion réussie"}


@router.post("/login")
async def login_for_frontend(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
    }


def generate_slug(name: str) -> str:
    """Génère un slug URL-friendly à partir du nom"""
    slug = name.lower().strip()
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Inscription avec création automatique du cabinet si c'est le premier utilisateur
    Inclut la sélection du pays et la validation selon les règles du pays
    """
    # 1. Valider le code pays
    if user_data.pays_code not in COUNTRY_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Code pays non supporté: {user_data.pays_code}"
        )
    
    country_info = get_country_info(user_data.pays_code)
    
    # 2. Valider les données de base
    # Email
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=400,
            detail="Format d'email invalide"
        )
    
    # Mot de passe
    valid_password, password_msg = validate_password_strength(user_data.password)
    if not valid_password:
        raise HTTPException(
            status_code=400,
            detail=password_msg
        )
    
    # Téléphone cabinet (si fourni)
    if user_data.telephone_cabinet:
        if not validate_phone(user_data.telephone_cabinet, user_data.pays_code):
            raise HTTPException(
                status_code=400,
                detail=f"Format de téléphone invalide. Format attendu: {country_info['phone_format']}"
            )
    
    # Identifiant d'entreprise (si fourni)
    if user_data.siret:
        if not validate_siret(user_data.siret, user_data.pays_code):
            raise HTTPException(
                status_code=400,
                detail=f"{country_info['company_id_name']} invalide"
            )
    
    # 3. Vérifier l'unicité
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur existe déjà"
        )
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà enregistré"
        )
    
    # 4. Vérifier si c'est le premier utilisateur (création du cabinet nécessaire)
    cabinet = None
    if user_data.cabinet_name:
        # Vérifier si le cabinet existe
        cabinet = db.query(Cabinet).filter(
            func.lower(Cabinet.nom) == user_data.cabinet_name.lower()
        ).first()
        
        if not cabinet:
            # Créer le cabinet avec les paramètres du pays
            cabinet_slug = generate_slug(user_data.cabinet_name)
            slug_count = db.query(Cabinet).filter(Cabinet.slug.like(f"{cabinet_slug}%")).count()
            if slug_count > 0:
                cabinet_slug = f"{cabinet_slug}-{slug_count + 1}"
            
            cabinet = Cabinet(
                nom=sanitize_string(user_data.cabinet_name),
                slug=cabinet_slug,
                siret=user_data.siret,
                telephone=user_data.telephone_cabinet,
                email=user_data.email,  # Email du cabinet = email du premier utilisateur
                adresse=sanitize_string(user_data.adresse) if user_data.adresse else None,
                code_postal=user_data.code_postal,
                ville=sanitize_string(user_data.ville) if user_data.ville else None,
                pays_code=user_data.pays_code,
                langue=f"fr-{user_data.pays_code}",
                fuseau_horaire=_get_timezone_for_country(user_data.pays_code),
                devise=country_info["currency"],
                format_date=country_info["date_format"],
                is_active=True,
                plan="trial",
                max_users=5,
                max_clients=50
            )
            
            # Extraire SIREN du SIRET pour la France
            if user_data.pays_code == "FR" and user_data.siret:
                cabinet.siren = user_data.siret[:9]
            
            db.add(cabinet)
            db.flush()
            
            # Le premier utilisateur devient admin
            user_data.role = "admin"
    
    # 5. Créer l'utilisateur
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        cabinet_name=cabinet.nom if cabinet else user_data.cabinet_name,
        cabinet_id=cabinet.id if cabinet else None,
        role=user_data.role,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 6. Créer le token pour connexion automatique
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "cabinet_id": user.cabinet_id,
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "cabinet_id": user.cabinet_id,
            "cabinet_name": user.cabinet_name
        },
        "cabinet": {
            "id": cabinet.id if cabinet else None,
            "nom": cabinet.nom if cabinet else user_data.cabinet_name,
            "pays_code": cabinet.pays_code if cabinet else user_data.pays_code,
            "devise": cabinet.devise if cabinet else country_info["currency"]
        } if cabinet else None,
        "access_token": access_token,
        "token_type": "bearer",
        "message": f"Bienvenue {'dans ' + cabinet.nom if cabinet else ''} !"
    }


def _get_timezone_for_country(country_code: str) -> str:
    """Retourne le fuseau horaire approprié pour un pays"""
    timezone_mapping = {
        "FR": "Europe/Paris",
        "CM": "Africa/Douala",
        "GA": "Africa/Libreville",
        "CG": "Africa/Brazzaville",
        "TD": "Africa/Ndjamena",
        "CF": "Africa/Bangui",
        "GQ": "Africa/Malabo",
        "SN": "Africa/Dakar",
        "CI": "Africa/Abidjan",
        "BF": "Africa/Ouagadougou",
        "ML": "Africa/Bamako",
        "TG": "Africa/Lome",
        "BJ": "Africa/Porto-Novo",
        "NE": "Africa/Niamey",
        "GW": "Africa/Bissau",
        "KM": "Indian/Comoro",
        "GN": "Africa/Conakry",
        "CD": "Africa/Kinshasa"
    }
    
    return timezone_mapping.get(country_code, "UTC")


@router.get("/countries")
async def get_countries_list():
    """
    Retourne la liste des pays disponibles pour l'inscription
    """
    countries = []
    
    for code, config in COUNTRY_CONFIGS.items():
        countries.append({
            "code": code,
            "name": config["name"],
            "currency": config["currency"],
            "company_id_label": config["company_id_name"],
            "phone_placeholder": config["phone_format"].split(" ou ")[0],
            "phone_format": config["phone_format"]
        })
    
    # Trier avec la France en premier, puis par nom
    countries.sort(key=lambda x: (x["code"] != "FR", x["name"]))
    
    return countries


async def get_current_user_websocket(token: str, db: Session = None):
    """
    Fonction pour authentifier un utilisateur via WebSocket
    Le token est passé directement dans l'URL
    """
    from app.core.database import SessionLocal
    
    if not db:
        db = SessionLocal()
        try:
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
            try:
                username = verify_token(token, credentials_exception)
            except JWTError:
                return None
            
            user = db.query(User).filter(User.username == username).first()
            return user
        finally:
            db.close()
    else:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            username = verify_token(token, credentials_exception)
        except JWTError:
            return None
        
        user = db.query(User).filter(User.username == username).first()
        return user