# src/app/routers/history.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime
from app.database.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/history", tags=["History"])


class HistoryItemResponse(BaseModel):
    audit_log_id: int
    session_id: str
    sequence_chat_id: int
    question: str
    created_at: datetime
    document_type_id: int
    document_number: str
    
    class Config:
        from_attributes = True


@router.get(
    "/",
    response_model=List[HistoryItemResponse],
    summary="Obtener historial de consultas del usuario"
)
def get_user_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de consultas del usuario autenticado.
    Requiere token JWT válido.
    """
    try:
        history = (
            db.query(AuditLog)
            .filter(AuditLog.user_id == current_user.user_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .all()
        )
        
        # Convertir session_id a string
        result = []
        for item in history:
            result.append({
                "audit_log_id": item.audit_log_id,
                "session_id": str(item.session_id),
                "sequence_chat_id": item.sequence_chat_id,
                "question": item.question,
                "created_at": item.created_at,
                "document_type_id": item.document_type_id,
                "document_number": item.document_number
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial: {str(e)}"
        )


@router.get(
    "/session/{session_id}",
    summary="Obtener consultas de una sesión específica"
)
def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las consultas de una sesión específica con sus respuestas.
    Solo retorna sesiones del usuario autenticado.
    """
    try:
        session_uuid = UUID(session_id)
        
        history = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == current_user.user_id,
                AuditLog.session_id == session_uuid
            )
            .order_by(AuditLog.sequence_chat_id.asc())
            .all()
        )
        
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada o no tienes acceso a ella"
            )
        
        # Retornar con respuestas
        result = []
        for item in history:
            result.append({
                "audit_log_id": item.audit_log_id,
                "session_id": str(item.session_id),
                "sequence_chat_id": item.sequence_chat_id,
                "question": item.question,
                "response": item.response_json,
                "created_at": item.created_at.isoformat(),
                "document_type_id": item.document_type_id,
                "document_number": item.document_number
            })
        
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id inválido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo historial de sesión: {str(e)}"
        )

