from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Cabinet(Base):
    __tablename__ = "cabinets"

    id = Column(Integer, primary_key=True, index=True)
    
    # Informations de base
    nom = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True, index=True)  # URL-friendly identifier
    
    # Informations légales
    siret = Column(String(14))
    siren = Column(String(9))
    numero_tva = Column(String)
    
    # Coordonnées
    adresse = Column(Text)
    code_postal = Column(String(5))
    ville = Column(String)
    telephone = Column(String)
    email = Column(String)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    max_users = Column(Integer, default=5)  # Limite d'utilisateurs
    max_clients = Column(Integer, default=100)  # Limite de clients
    
    # Abonnement
    plan = Column(String, default="standard")  # basic, standard, premium
    date_expiration = Column(DateTime(timezone=True))
    
    # Localisation et configuration
    pays_code = Column(String(2), nullable=False, default="FR")  # Code ISO du pays
    langue = Column(String(5), nullable=False, default="fr-FR")  # Langue préférée
    fuseau_horaire = Column(String(50), nullable=False, default="Europe/Paris")
    devise = Column(String(3), nullable=False, default="EUR")  # Code devise ISO
    format_date = Column(String(20), nullable=False, default="DD/MM/YYYY")
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    users = relationship("User", back_populates="cabinet", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="cabinet", cascade="all, delete-orphan")
    dossiers = relationship("Dossier", back_populates="cabinet", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cabinet {self.nom} ({self.slug})>"