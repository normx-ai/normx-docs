"""
Schémas Pydantic pour les notifications
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NotificationBase(BaseModel):
    title: str
    message: str
    type_notification: str = "in_app"


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    alerte_id: Optional[int] = None
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int
    total: int


class NotificationCreate(NotificationBase):
    user_id: int
    alerte_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    is_read: bool