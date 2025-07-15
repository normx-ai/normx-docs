from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    cabinet_id = Column(Integer, ForeignKey("cabinets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    alerte_id = Column(Integer, ForeignKey("alertes.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type_notification = Column(String)  # email, in_app, sms
    is_read = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    
    # Relations
    cabinet = relationship("Cabinet", backref="notifications")
    user = relationship("User")
    alerte = relationship("Alerte", backref="notifications")