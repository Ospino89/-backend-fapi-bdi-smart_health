# src/app/services/vector_search.py

from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.schemas.rag import SimilarChunk
from app.services.llm_client import get_embedding
from app.database.database import SessionLocal

"""
Este módulo construye el contexto RAG y las `sources` a partir de los resultados
de `search_similar_chunks`, que devuelve una lista de `SimilarChunk` con:
  - chunk_text
  - source_type
  - source_id
  - patient_id
  - date
  - relevance_score
"""

# Constantes de configuración para P3-4
DEFAULT_TOP_K = 15
MAX_PER_TABLE = 10
DEFAULT_YEARS_BACK = 5  # Filtro temporal: últimos 5 años
DEFAULT_MIN_SCORE = 0.3  # Score mínimo de relevancia

async def search_similar_chunks(
    patient_id: int,
    question: str,
    k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    allowed_sources: list[str] | None = None,  # Opcional: filtrar por tipo de registro
) -> List[SimilarChunk]:
    """
    Devuelve los k chunks más relevantes para la pregunta de un paciente.
    """
    # 1) Obtener embedding de la pregunta
    question_embedding = await get_embedding(question)

    db: Session = SessionLocal()
    try:
        chunks: List[SimilarChunk] = []

        # Si la tabla no tiene reason_embedding, devolvemos lista vacía sin romper
        try:
            sql_appointments = text(
                """
                SELECT
                    appointment_id                                 AS source_id,
                    patient_id                                     AS patient_id,
                    reason                                         AS text,
                    appointment_date                               AS date,
                    0.0                                            AS relevance_score
                FROM smart_health.appointments
                WHERE patient_id = :patient_id
                    AND appointment_date >= NOW() - INTERVAL '5 years'
                ORDER BY appointment_date DESC
                LIMIT :k
                """
            )

            rows = db.execute(
                sql_appointments,
                {
                    "patient_id": patient_id,
                    "q_emb": question_embedding,  # no se usa en el SQL pero se mantiene firma
                    "k": min(k, MAX_PER_TABLE),
                },
            ).fetchall()

            for row in rows:
                chunks.append(
                    SimilarChunk(
                        source_type="appointment",
                        source_id=row.source_id,
                        patient_id=row.patient_id,
                        chunk_text=row.text,
                        date=row.date,
                        relevance_score=float(row.relevance_score),
                    )
                )
        except Exception:
            # Si falla (por columnas que no existen, etc.), no lanzamos error: dejamos chunks = []
            chunks = []

        # 1. Filtrar por score mínimo
        chunks = [c for c in chunks if c.relevance_score >= min_score]

        # 2. Filtrar por tipo de registro si se especificó
        if allowed_sources is not None:
            chunks = [c for c in chunks if c.source_type in allowed_sources]

        # 3. Ordenar por score y aplicar k global
        chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        chunks = chunks[:k]

        return chunks

    finally:
        db.close()

    """
    Devuelve los k chunks más relevantes para la pregunta de un paciente.
    
    Args:
        patient_id: ID del paciente
        question: Pregunta del usuario
        k: Número máximo de chunks a devolver (por defecto 15)
        min_score: Score mínimo de relevancia (por defecto 0.3)
        allowed_sources: Lista opcional de tipos de fuente permitidos 
                        (ej: ["diagnosis", "appointment"])
    
    Returns:
        Lista de SimilarChunk ordenados por relevancia
    """

    # 1) Obtener embedding de la pregunta
    question_embedding = await get_embedding(question)

    db: Session = SessionLocal()
    try:
        chunks: List[SimilarChunk] = []

        # Consulta para appointments con filtro de fecha
        sql_appointments = text(
            """
            SELECT
                appointment_id                                 AS source_id,
                patient_id                                     AS patient_id,
                reason                                         AS text,
                appointment_date                               AS date,
                1 - (reason_embedding <-> :q_emb)             AS relevance_score
            FROM smart_health.appointments
            WHERE patient_id = :patient_id
                AND reason_embedding IS NOT NULL
                AND appointment_date >= NOW() - INTERVAL '5 years'
            ORDER BY reason_embedding <-> CAST(:q_emb AS vector)
            LIMIT :k
            """
        )

        rows = db.execute(
            sql_appointments,
            {
                "patient_id": patient_id,
                "q_emb": question_embedding,
                "k": min(k, MAX_PER_TABLE),
            },
        ).fetchall()

        for row in rows:
            chunks.append(
                SimilarChunk(
                    source_type="appointment",
                    source_id=row.source_id,
                    patient_id=row.patient_id,
                    chunk_text=row.text,
                    date=row.date,
                    relevance_score=float(row.relevance_score),
                )
            )

        # TODO: Agregar consultas similares para diagnoses, prescriptions, etc.
        # Ejemplo para diagnoses:
        # sql_diagnoses = text("""
        #     SELECT
        #         diagnosis_id AS source_id,
        #         patient_id,
        #         diagnosis_code || ' - ' || description AS text,
        #         diagnosis_date AS date,
        #         1 - (diagnosis_embedding <-> :q_emb) AS relevance_score
        #     FROM smart_health.diagnoses
        #     WHERE patient_id = :patient_id
        #         AND diagnosis_embedding IS NOT NULL
        #         AND diagnosis_date >= NOW() - INTERVAL '5 years'
        #     ORDER BY diagnosis_embedding <-> CAST(:q_emb AS vector)
        #     LIMIT :k
        # """)

        # 1. Filtrar por score mínimo
        chunks = [
            c for c in chunks
            if c.relevance_score >= min_score
        ]

        # 2. Filtrar por tipo de registro si se especificó
        if allowed_sources is not None:
            chunks = [c for c in chunks if c.source_type in allowed_sources]

        # 3. Ordenar por score y aplicar k global
        chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        chunks = chunks[:k]
        
        return chunks

    finally:
        db.close()