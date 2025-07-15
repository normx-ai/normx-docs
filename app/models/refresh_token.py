"""
Modèle pour la gestion des refresh tokens
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from app.core.database import Base


class RefreshToken(Base):
    """Stockage sécurisé des refresh tokens"""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Informations de sécurité
    device_id = Column(String)  # Identifiant du device/navigateur
    ip_address = Column(String)  # IP de création
    user_agent = Column(String)  # User agent du navigateur
    
    # Gestion du cycle de vie
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True))
    
    # Relations
    user = relationship("User", backref="refresh_tokens")
    
    # Index pour les requêtes fréquentes
    __table_args__ = (
        Index('idx_refresh_token_user_active', 'user_id', 'revoked'),
        Index('idx_refresh_token_expires', 'expires_at'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Vérifie si le token est expiré"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Vérifie si le token est valide (non révoqué et non expiré)"""
        return not self.revoked and not self.is_expired
    
    def revoke(self):
        """Révoque le token"""
        self.revoked = True
        self.revoked_at = datetime.utcnow()