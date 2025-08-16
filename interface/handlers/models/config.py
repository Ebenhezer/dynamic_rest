from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BIGINT, FLOAT, JSON, VARCHAR
from database import Base

class Config(Base):
    __tablename__ = "t_config"
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    config_username = Column(String)
    config_password = Column(String)
    config_email = Column(String)
    smtp_server_address = Column(String)
    sender_email_address = Column(String)
    smtp_password = Column(String)
    smtp_username = Column(String)
    smtp_port = Column(Integer)
    domain = Column(String)
    account_role = Column(String)