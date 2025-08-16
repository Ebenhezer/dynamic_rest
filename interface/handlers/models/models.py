from pydantic import BaseModel
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, BIGINT, FLOAT, JSON, VARCHAR
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declarative_base
from handlers.models.user import User

Base = declarative_base()

def create_dynamic_table(table_name, columns, extend_existing):
    class DynamicTable(Base):
        __tablename__ = table_name
        id = Column(Integer, primary_key=True, index=True)
        __table_args__ = {'extend_existing': extend_existing}  # Add this line
        # Create columns dynamically
        for column_name, column_type in columns.items():
            exec(f"{column_name} = Column({column_type})")

    return DynamicTable

class Interface(Base):
    __tablename__ = "t_dynamic_interface"
    id  = Column(BIGINT, primary_key=True, nullable=False, autoincrement=True)
    interface_id = Column(Integer, unique=True)
    interface_url = Column(String)
    interface_token = Column(String)
    interface_description = Column(String)
    table_name = Column(String)
    fields = Column(ARRAY(JSON)) 
    interface_details = Column(JSON(300))
    update_period = Column(BIGINT)
    last_modified = Column(BIGINT)
    actual_update_time = Column(BIGINT)
    notification_sent = Column(Boolean)
    notification_enabled = Column(Boolean)
    last_notification_status = Column(String)
    whatsapp_enabled = Column(Boolean)
    sms_enabled = Column(Boolean)
    notification_users = Column(JSON(10000))
    interface_owner = Column(BIGINT, ForeignKey(User.user_id))
