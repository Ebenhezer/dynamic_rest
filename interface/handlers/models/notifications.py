from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BIGINT, FLOAT, JSON, TEXT
from sqlalchemy.orm import relationship

from database import Base
from handlers.models.user import User

class Notification(Base):
    __tablename__ = "t_notification_history"
    id  = Column(BIGINT, primary_key=True, nullable=False, autoincrement=True)
    device_id = Column(BIGINT)
    device_name = Column(TEXT)
    device_type = Column(TEXT)
    notification_message = Column(TEXT) 
    notification_time = Column(BIGINT)
    notification_owner = Column(BIGINT, ForeignKey(User.user_id))