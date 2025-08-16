
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BIGINT, FLOAT, JSON, VARCHAR, DateTime
from fastapi import Body
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from database import Base
from handlers.models.user import User
from datetime import datetime

class SharedDeviceLink(Base):
    __tablename__ = "t_shared_devices"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String, unique=True, nullable=False)
    device_id = Column(BIGINT, nullable=False)
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    email = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    history_days = Column(Integer, nullable=False)
    created_at = Column(BIGINT, default=lambda: int(datetime.utcnow().timestamp()))
    expires_at = Column(BIGINT, nullable=True)
    revoked = Column(Boolean, default=False)
    device_owner = Column(BIGINT, ForeignKey("t_user_info.user_id"))
    shared_with_id = Column(BIGINT, ForeignKey("t_user_info.user_id"))
    access_level = Column(String, nullable=False)
    comment = Column(String, nullable=True)