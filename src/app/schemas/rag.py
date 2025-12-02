# src/app/schemas/rag.py
from datetime import datetime
from pydantic import BaseModel

class SimilarChunk(BaseModel):
    source_type: str          # "appointment", "diagnosis", "medical_record", "medication"
    source_id: int            # id de la fila en su tabla
    patient_id: int
    chunk_text: str                 # texto que verá el LLM
    date: datetime | None = None
    relevance_score: float    # mientras más alto, más relevante