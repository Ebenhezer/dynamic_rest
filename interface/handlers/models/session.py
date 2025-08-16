from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BIGINT
from sqlalchemy.orm import relationship
from handlers.models.user import User
from database import Base

class Session(Base):
    __tablename__ = "t_session"
    id  = Column(BIGINT, primary_key=True, nullable=False, autoincrement=True)
    session_id = Column(String, primary_key=True, nullable=False)
    user_id = Column(BIGINT, ForeignKey(User.user_id))
    session_ip_address = Column(String(150))
    session_start_time = Column(BIGINT)
    session_end_time = Column(BIGINT)
    session_duration = Column(BIGINT)
    user_agent = Column(String(150))
    device_type = Column(String(150))
    referrer = Column(String(50))
    session_status = Column(Boolean(50))
    session_location = Column(String(50))
    session_error_log = Column(String(50))
    session_data = Column(String(500))