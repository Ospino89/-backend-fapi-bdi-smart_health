# src/app/routers/catalog.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import logging

from app.database.database import get_db
from app.schemas.catalog import DocumentTypeResponse

router = APIRouter(
    prefix="/catalog",
    tags=["Catalog"]
)

logger = logging.getLogger(__name__)


@router.get(
    "/document-types",
    response_model=List[DocumentTypeResponse],
    summary="Obtener todos los tipos de documento",
    description="Retorna la lista completa de tipos de documento disponibles en el sistema"
)
def get_document_types(db: Session = Depends(get_db)):
    """
    Obtiene todos los tipos de documento disponibles en la base de datos.
    No requiere autenticación ya que es información pública del catálogo.
    """
    try:
        # Consultar tipos de documento desde la base de datos
        result = db.execute(text("""
            SELECT 
                document_type_id,
                type_name,
                type_code,
                description
            FROM smart_health.document_types
            ORDER BY document_type_id
        """))
        
        document_types = []
        for row in result:
            document_types.append({
                "document_type_id": row[0],
                "type_name": row[1],
                "type_code": row[2] if row[2] else None,
                "description": row[3] if row[3] else None
            })
        
        return document_types
        
    except Exception as e:
        logger.error(f"Error obteniendo tipos de documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tipos de documento: {str(e)}"
        )

