# app/db/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


# ============================================================
#                   USER SCHEMAS
# ============================================================

class UserBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    first_surname: str
    second_surname: Optional[str] = None
    email: EmailStr


class UserCreate(UserBase):
    password: str   # Se recibe en texto plano


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    user_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # permite convertir desde modelos ORM


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================
#                   AUDIT LOGS SCHEMAS
# ============================================================

class AuditLogBase(BaseModel):
    session_id: UUID
    sequence_chat_id: int
    document_type_id: int
    document_number: str
    question: str
    response_json: Any  # JSONB
    


class AuditLogCreate(AuditLogBase):
    user_id: int


class AuditLogResponse(AuditLogBase):
    audit_log_id: int
    created_at: datetime

    class Config:
        from_attributes = True
