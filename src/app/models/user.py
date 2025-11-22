from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.database import Base
from .audit_logs import AuditLog



class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "smart_health"}

    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    first_surname = Column(String(50), nullable=False)
    second_surname = Column(String(50), nullable=True)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # relación con audit_logs
    audit_logs = relationship("AuditLog", back_populates="user")

