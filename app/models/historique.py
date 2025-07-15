from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class HistoriqueDossier(Base):
    __tablename__ = "historique_dossiers"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # creation, status_change, document_added, etc.
    old_value = Column(Text)
    new_value = Column(Text)
    commentaire = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    cabinet = relationship("Cabinet", backref="historique_dossiers")
    dossier = relationship("Dossier", back_populates="historique")
    user = relationship("User")