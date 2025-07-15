from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    username = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    
    # Informations du cabinet (optionnelles)
    siret = Column(String(14))
    siren = Column(String(9))
    nom_gerant = Column(String)
    adresse_cabinet = Column(String)
    code_postal = Column(String(5))
    ville = Column(String)
    telephone_cabinet = Column(String)
    email_cabinet = Column(String)
    site_web = Column(String)
    
    role = Column(String, default="collaborateur")  # admin, manager, collaborateur
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    cabinet = relationship("Cabinet", back_populates="users")
    
    # Contrainte unique pour username par cabinet
    __table_args__ = (
        UniqueConstraint('cabinet_id', 'username', name='uq_user_cabinet_username'),
    )