"""
Dépendances communes pour les API
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.api.auth import oauth2_scheme


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Récupère l'utilisateur courant à partir du token JWT"""
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


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Vérifie que l'utilisateur est actif"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user


def get_current_cabinet_id(current_user: User = Depends(get_current_active_user)) -> int:
    """Récupère le cabinet_id de l'utilisateur courant"""
    return current_user.cabinet_id


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    """Récupère l'utilisateur courant si un token est fourni, sinon retourne None"""
    if not token:
        return None
    
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None