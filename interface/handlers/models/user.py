from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BIGINT
from sqlalchemy.orm import relationship

from database import Base

class User(Base):
    __tablename__ = "t_user_info"
    user_id = Column(BIGINT, primary_key=True, nullable=False, autoincrement=True)
    username = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    user_password = Column(String(150), nullable=False)
    gender = Column(String(50), nullable=False)
    date_of_birth = Column(String(50))
    country_of_birth = Column(String(50))
    cellphone_number = Column(String(50), nullable=False)
    last_login = Column(String(50))
    api_key  = Column(String(50))
    api_key_gen_time = Column(String(50))
    verification_link = Column(String(150))
    account_active = Column(Boolean)
    account_verified = Column(Boolean)
    account_type = Column(Integer)
    reset_password_token = Column(String(50))
    profile_pic = Column(String(50))
    cellphone_code = Column(Integer)
    cellphone_verified = Column(Boolean)
    time_offset = Column(Integer)
    address_line_1 = Column(String(150))
    address_line_2 = Column(String(150))
    address_postal_code = Column(Integer)
    address_state = Column(String(150))
    address_country = Column(String(50))
    whatsapp_messages = Column(BIGINT)
    sms_messages = Column(BIGINT)
    verification_counter = Column(BIGINT)
    verification_time = Column(BIGINT)
    api_calls = Column(BIGINT)
