from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    nom = Column(String, nullable=False, index=True)
    numero_client = Column(String, index=True)  # Unique par cabinet, pas globalement
    email = Column(String)
    telephone = Column(String)
    adresse = Column(String)
    ville = Column(String)
    code_postal = Column(String)
    siret = Column(String)
    forme_juridique = Column(String)  # SARL, SASU, SAS, EI, EURL, SNC
    nom_gerant = Column(String)
    telephone_gerant = Column(String)
    email_gerant = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Utilisateur responsable du client
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    responsable = relationship("User", backref="clients_geres")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    cabinet = relationship("Cabinet", back_populates="clients")
    
    # Contrainte unique pour numero_client par cabinet
    __table_args__ = (
        UniqueConstraint('cabinet_id', 'numero_client', name='uq_client_cabinet_numero'),
    )