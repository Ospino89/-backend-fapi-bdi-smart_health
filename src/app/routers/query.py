# src/app/routers/query.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from sqlalchemy.orm import Session
import logging
import time

from app.services.llm_service import llm_service
from app.services.clinical_service import fetch_patient_and_records
from app.services.vector_search import search_similar_chunks
from app.database.database import get_db
from app.schemas.clinical import PatientInfo, ClinicalRecords

router = APIRouter(prefix="/query", tags=["RAG Query"])
logger = logging.getLogger(__name__)

# === SCHEMAS ===

class QueryInput(BaseModel):
    user_id: str
    session_id: str
    document_type_id: int
    document_number: str
    question: str

class QuerySuccess(BaseModel):
    status: Literal["success"] = "success"
    data: Dict

class QueryNoData(BaseModel):
    status: Literal["no_data"] = "no_data"
    message: str
    metadata: Optional[Dict] = None

class QueryError(BaseModel):
    status: Literal["error"] = "error"
    error: Dict


# === CONTEXTO ===

def build_context_from_real_data(
    patient_info: PatientInfo,
    clinical_records: ClinicalRecords,
    similar_chunks: List
) -> str:

    # Calcular edad porque NO existe en BD
    age = None
    if patient_info.birth_date:
        from datetime import date
        today = date.today()
        age = today.year - patient_info.birth_date.year - (
            (today.month, today.day) < (patient_info.birth_date.month, patient_info.birth_date.day)
        )

    context = f"""### INFORMACIÓN BÁSICA DEL PACIENTE
Nombre: {patient_info.first_name} {patient_info.first_surname}
Edad: {age if age is not None else 'No disponible'}
Documento: {patient_info.document_number}
Género: {patient_info.gender}
Email: {patient_info.email or 'No registrado'}

"""

    # CITAS
    if clinical_records.appointments:
        context += "### CITAS MÉDICAS RECIENTES\n"
        for apt in clinical_records.appointments[:10]:
            context += f"""- Fecha: {apt.appointment_date}
  Estado: {apt.status}
  Motivo: {apt.reason or 'No especificado'}

"""

    # REGISTROS
    if clinical_records.medical_records:
        context += "### REGISTROS MÉDICOS\n"
        for rec in clinical_records.medical_records[:10]:
            context += f"""- Fecha: {rec.registration_datetime}
  Tipo: {rec.record_type}
  Descripción: {rec.description or 'Sin descripción'}

"""

    # PRESCRIPCIONES
    if clinical_records.prescriptions:
        context += "### MEDICAMENTOS Y PRESCRIPCIONES\n"
        for presc in clinical_records.prescriptions[:15]:
            context += f"- {presc.medication_name}: {presc.dosage} - {presc.frequency}\n"
            if presc.duration:
                context += f"  Duración: {presc.duration}\n"
            if presc.notes:
                context += f"  Notas: {presc.notes}\n"
        context += "\n"

    # DIAGNÓSTICOS
    if clinical_records.diagnoses:
        context += "### DIAGNÓSTICOS\n"
        for diag in clinical_records.diagnoses[:15]:
            context += f"- {diag.description} (Código ICD: {diag.icd_code})\n"
            context += f"  Tipo: {diag.diagnosis_type}\n"
            if diag.note:
                context += f"  Nota: {diag.note}\n"
        context += "\n"

    # VECTOR SEARCH
    if similar_chunks:
        context += "### INFORMACIÓN ADICIONAL RELEVANTE (BÚSQUEDA SEMÁNTICA)\n"
        for chunk in similar_chunks[:5]:
            context += f"- [Relevancia: {chunk.relevance_score:.2f}] {chunk.chunk_text}\n"
            context += f"  Fuente: {chunk.source_type} - Fecha: {chunk.date}\n\n"

    return context


# === SOURCES ===

def build_sources_from_real_data(clinical_records: ClinicalRecords, similar_chunks: List) -> List[Dict]:
    sources = []

    for apt in clinical_records.appointments[:5]:
        sources.append({
            "type": "clinical_record",
            "source_id": str(apt.appointment_id),
            "source_type": "appointment",
            "date": str(apt.appointment_date)
        })

    for presc in clinical_records.prescriptions[:5]:
        sources.append({
            "type": "clinical_record",
            "source_id": str(presc.prescription_id),
            "source_type": "prescription",
            "date": str(presc.prescription_date)
        })

    for chunk in similar_chunks[:5]:
        sources.append({
            "type": "vector_search",
            "source_id": str(chunk.source_id),
            "source_type": chunk.source_type,
            "relevance_score": chunk.relevance_score,
            "date": str(chunk.date) if chunk.date else None
        })

    return sources


# === ENDPOINT PRINCIPAL ===

@router.post("/", response_model=QuerySuccess | QueryNoData | QueryError)
async def query_patient(input_data: QueryInput, db: Session = Depends(get_db)):
    start_time = time.time()

    try:
        logger.info(f"📝 Pregunta: {input_data.question}")
        logger.info(f"👤 Documento: {input_data.document_type_id}-{input_data.document_number}")

        # 1. BUSCAR PACIENTE
        patient_info, clinical_data = fetch_patient_and_records(
            db=db,
            document_type_id=input_data.document_type_id,
            document_number=input_data.document_number
        )

        if not patient_info:
            return QueryError(
                status="error",
                error={
                    "code": "PATIENT_NOT_FOUND",
                    "message": "No se encontró un paciente con el documento proporcionado",
                    "details": {
                        "document_type_id": input_data.document_type_id,
                        "document_number": input_data.document_number
                    }
                }
            )

        # 2. VECTOR SEARCH
        try:
            similar_chunks = await search_similar_chunks(
                patient_id=patient_info.patient_id,
                question=input_data.question,
                k=15,
                min_score=0.3
            )
        except:
            similar_chunks = []

        # 3. CONTEXTO
        context = build_context_from_real_data(
            patient_info=patient_info,
            clinical_records=clinical_data.records,
            similar_chunks=similar_chunks
        )

        # Si NO hay datos reales
        if not clinical_data.has_data and len(similar_chunks) == 0:
            return QueryNoData(
                status="no_data",
                message="No hay datos clínicos relevantes para este paciente",
                metadata={
                    "patient_id": patient_info.patient_id,
                    "patient_name": f"{patient_info.first_name} {patient_info.first_surname}",
                    "query_time_ms": int((time.time() - start_time) * 1000)
                }
            )

        # 4. LLM
        llm_response = await llm_service.run_llm(
            question=input_data.question,
            context=context
        )

        response_status = llm_service.determine_status(llm_response.text, context)

        if response_status == "no_data":
            return QueryNoData(
                status="no_data",
                message=llm_response.text,
                metadata={
                    "patient_id": patient_info.patient_id,
                    "model_used": llm_response.model_used,
                    "query_time_ms": int((time.time() - start_time) * 1000)
                }
            )

        # 5. RESPUESTA FINAL
        sources = build_sources_from_real_data(clinical_data.records, similar_chunks)

        response_data = {
            "patient": {
                "patient_id": patient_info.patient_id,
                "name": f"{patient_info.first_name} {patient_info.first_surname}",
                "document": patient_info.document_number
            },
            "answer": {
                "text": llm_response.text,
                "confidence": llm_response.confidence,
                "model_used": llm_response.model_used
            },
            "sources": sources,
            "metadata": {
                "total_records_analyzed": (
                    len(clinical_data.records.appointments) +
                    len(clinical_data.records.medical_records) +
                    len(clinical_data.records.prescriptions) +
                    len(clinical_data.records.diagnoses) +
                    len(similar_chunks)
                ),
                "appointments_count": len(clinical_data.records.appointments),
                "prescriptions_count": len(clinical_data.records.prescriptions),
                "diagnoses_count": len(clinical_data.records.diagnoses),
                "vector_chunks_count": len(similar_chunks),
                "context_length": len(context),
                "tokens_used": llm_response.tokens_used,
                "query_time_ms": int((time.time() - start_time) * 1000)
            }
        }

        return QuerySuccess(status="success", data=response_data)

    except Exception as e:
        logger.exception("❌ Error inesperado")
        return QueryError(
            status="error",
            error={
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
                "details": {"error": str(e)}
            }
        )
