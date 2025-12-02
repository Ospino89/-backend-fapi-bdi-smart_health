# src/app/routers/query.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(
    prefix="/query",
    tags=["Query"],
)


@router.post(
    "",
    summary="Ejecutar consulta de usuario",
)
def execute_query(payload: QueryRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == payload.user_id).first()

    # Si no existe usuario, devolvemos datos dummy
    if not user:
        dummy = QueryResponse(
            user_id=payload.user_id,
            email="test@example.com",
            first_name="Test",
            middle_name=None,
            first_surname="User",
            second_surname=None,
            is_active=True,
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )
        return {
            "status": "no_data",
            "data": dummy.model_dump(),
            "answer": "Sin datos clínicos para este paciente.",
        }

    resp = QueryResponse(
        user_id=user.user_id,
        email=user.email,
        first_name=user.first_name,
        middle_name=user.middle_name,
        first_surname=user.first_surname,
        second_surname=user.second_surname,
        is_active=user.is_active,
        created_at=str(user.created_at),
        updated_at=str(user.updated_at),
    )

    return {
        "status": "success",
        "data": resp.model_dump(),
        "answer": "Respuesta generada correctamente.",
    }
