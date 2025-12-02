from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    user_id: int = Field(..., description="ID del usuario que realiza la consulta")
    session_id: Optional[str] = Field(None, description="ID de sesión")
    document_type_id: Optional[str] = Field(  # ← antes era int
        None,
        description="Tipo de documento del paciente (ej. 'CC')",
    )
    document_number: Optional[str] = Field(
        None, description="Número de documento del paciente"
    )
    question: str = Field(
        ...,
        min_length=3,
        description="Pregunta realizada por el usuario",
    )

    class Config:
        extra = "forbid"


class QueryResponse(BaseModel):
    user_id: int
    email: str
    first_name: str
    middle_name: Optional[str]
    first_surname: str
    second_surname: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True
