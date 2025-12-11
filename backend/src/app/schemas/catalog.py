# src/app/schemas/catalog.py

from pydantic import BaseModel
from typing import Optional


class DocumentTypeResponse(BaseModel):
    """Schema para respuesta de tipo de documento"""
    document_type_id: int
    type_name: str
    type_code: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

