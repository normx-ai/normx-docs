from sqlalchemy import Column, Integer, String, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TypeService(str, enum.Enum):
    COMPTABILITE = "COMPTABILITE"
    TVA = "TVA"
    PAIE = "PAIE"
    JURIDIQUE = "JURIDIQUE"
    FISCAL = "FISCAL"
    SOCIAL = "SOCIAL"
    AUDIT = "AUDIT"
    CONSEIL = "CONSEIL"
    AUTRE = "AUTRE"


# Table d'association pour la relation many-to-many entre Dossier et Service
dossier_services = Table(
    'dossier_services',
    Base.metadata,
    Column('dossier_id', Integer, ForeignKey('dossiers.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True)
)


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    type_service = Column(Enum(TypeService), unique=True, nullable=False)
    nom = Column(String, nullable=False)
    description = Column(String)
    
    # Relations
    # dossiers = relationship("Dossier", secondary=dossier_services, back_populates="services")  # Commenté car services commenté dans Dossier