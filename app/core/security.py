from datetime import datetime, timedelta
from typing import Optional, Tuple
import re
import unicodedata
from functools import wraps
import secrets
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.validators import (
    validate_phone as validate_phone_intl,
    validate_company_id,
    validate_iban as validate_iban_intl,
    format_phone_number,
    get_country_info,
    get_supported_countries,
    get_currency_symbol
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration du rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri=settings.REDIS_URL,
    strategy="moving-window"
)

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Gestionnaire personnalisé pour les erreurs de rate limiting
    """
    response = JSONResponse(
        {"detail": f"Limite de taux dépassée: {exc.detail}"}, 
        status_code=429
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    return response


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ========== GESTION DES REFRESH TOKENS ==========

def generate_refresh_token() -> str:
    """Génère un refresh token sécurisé"""
    return secrets.token_urlsafe(32)


def create_refresh_token(
    user_id: int,
    db: Session,
    device_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[str, datetime]:
    """
    Crée un nouveau refresh token pour un utilisateur
    
    Returns:
        Tuple (token, expiration_date)
    """
    from app.models.refresh_token import RefreshToken
    
    # Générer le token
    token = generate_refresh_token()
    
    # Calculer l'expiration
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Créer l'enregistrement en base
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        device_id=device_id,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    
    return token, expires_at


def verify_refresh_token(token: str, db: Session) -> Optional[int]:
    """
    Vérifie un refresh token et retourne l'ID utilisateur si valide
    """
    from app.models.refresh_token import RefreshToken
    
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.revoked == False
    ).first()
    
    if not refresh_token or refresh_token.is_expired:
        return None
    
    # Mettre à jour la dernière utilisation
    refresh_token.last_used_at = datetime.utcnow()
    db.commit()
    
    return refresh_token.user_id


def revoke_refresh_token(token: str, db: Session) -> bool:
    """Révoque un refresh token"""
    from app.models.refresh_token import RefreshToken
    
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if refresh_token:
        refresh_token.revoke()
        db.commit()
        return True
    
    return False


def revoke_all_user_tokens(user_id: int, db: Session, except_token: Optional[str] = None):
    """Révoque tous les refresh tokens d'un utilisateur"""
    from app.models.refresh_token import RefreshToken
    
    query = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    )
    
    if except_token:
        query = query.filter(RefreshToken.token != except_token)
    
    query.update({"revoked": True, "revoked_at": datetime.utcnow()})
    db.commit()


def cleanup_expired_tokens(db: Session) -> int:
    """Nettoie les tokens expirés de la base de données"""
    from app.models.refresh_token import RefreshToken
    
    result = db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()
    
    db.commit()
    return result


# ========== VALIDATION DES ENTRÉES ==========

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force d'un mot de passe
    Retourne (True, "") si valide, sinon (False, message d'erreur)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial"
    
    return True, ""


def validate_email(email: str) -> bool:
    """
    Valide le format d'une adresse email
    """
    email_pattern = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    return email_pattern.match(email) is not None


def validate_phone(phone: str, country_code: str = "FR") -> bool:
    """
    Valide un numéro de téléphone selon le pays
    Utilise le validateur international
    """
    return validate_phone_intl(phone, country_code)


def validate_siret(siret: str, country_code: str = "FR") -> bool:
    """
    Valide un identifiant d'entreprise selon le pays
    Pour la France : SIRET (14 chiffres avec algorithme de Luhn)
    Pour d'autres pays : utilise validate_company_id
    """
    return validate_company_id(siret, country_code)


def sanitize_string(text: str, max_length: int = 255) -> str:
    """
    Nettoie une chaîne de caractères pour éviter les injections
    """
    if not text:
        return ""
    
    # Supprime les caractères de contrôle
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    
    # Limite la longueur
    text = text[:max_length]
    
    # Supprime les espaces multiples
    text = " ".join(text.split())
    
    return text.strip()


def validate_date_format(date_str: str) -> bool:
    """
    Valide le format d'une date (YYYY-MM-DD)
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_iban(iban: str, country_code: Optional[str] = None) -> bool:
    """
    Valide un IBAN selon le pays
    """
    return validate_iban_intl(iban, country_code)


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """
    Valide l'extension d'un fichier
    """
    if not filename or "." not in filename:
        return False
    
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in allowed_extensions


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """
    Valide la taille d'un fichier (en bytes)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return 0 < file_size <= max_size_bytes


# ========== DÉCORATEURS DE SÉCURITÉ ==========

def require_strong_password(func):
    """
    Décorateur pour exiger un mot de passe fort
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        password = kwargs.get("password") or (args[0] if args else None)
        if password:
            valid, message = validate_password_strength(password)
            if not valid:
                raise HTTPException(status_code=400, detail=message)
        return await func(*args, **kwargs)
    return wrapper


def sanitize_inputs(params: list[str]):
    """
    Décorateur pour nettoyer automatiquement les entrées
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for param in params:
                if param in kwargs and isinstance(kwargs[param], str):
                    kwargs[param] = sanitize_string(kwargs[param])
            return await func(*args, **kwargs)
        return wrapper
    return decorator