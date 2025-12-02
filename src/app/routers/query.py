# src/app/routers/query.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
import logging
import time

from app.services.llm_service import llm_service

# Importar funciones de Persona 2 (ajusta según tus archivos reales)
# from app.services.patient_service import get_patient_by_document, get_clinical_records

router = APIRouter(prefix="/query", tags=["RAG Query"])
logger = logging.getLogger(__name__)

# === SCHEMAS ===

class QueryInput(BaseModel):
    """Input del endpoint /query"""
    user_id: str = Field(..., description="ID del usuario que hace la consulta")
    session_id: str = Field(..., description="ID de la sesión")
    document_type_id: int = Field(..., description="Tipo de documento (1=CC, 2=TI, etc)")
    document_number: str = Field(..., description="Número de documento del paciente")
    question: str = Field(..., description="Pregunta clínica")

class Source(BaseModel):
    """Fuente de información"""
    type: Literal["clinical_record", "vector_search"]
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    relevance_score: Optional[float] = None
    date: Optional[str] = None

class Metadata(BaseModel):
    """Metadatos de la consulta"""
    total_records_analyzed: int
    query_time_ms: int
    sources_used: int
    context_tokens: int
    model_used: str

class QuerySuccess(BaseModel):
    """Respuesta exitosa"""
    status: Literal["success"] = "success"
    data: Dict

class QueryNoData(BaseModel):
    """Respuesta sin datos"""
    status: Literal["no_data"] = "no_data"
    message: str
    metadata: Optional[Dict] = None

class QueryError(BaseModel):
    """Respuesta de error"""
    status: Literal["error"] = "error"
    error: Dict

# === FUNCIONES AUXILIARES (MOCK TEMPORAL) ===

def get_patient_by_document_mock(document_type_id: int, document_number: str):
    """MOCK de Persona 2 - Reemplaza con tu función real"""
    # TODO: Reemplazar con tu función real de Persona 2
    return {
        "patient_id": 1,
        "name": "Juan Pérez",
        "age": 45,
        "document_type": document_type_id,
        "document_number": document_number
    }

def get_clinical_records_mock(patient_id: int):
    """MOCK de Persona 2 - Reemplaza con tu función real"""
    # TODO: Reemplazar con tus funciones reales de Persona 2
    return {
        "appointments": [
            {
                "id": "APT-001",
                "date": "2024-11-20",
                "doctor": "Dr. García",
                "diagnosis": "Hipertensión arterial controlada",
                "notes": "Paciente con buen control de presión arterial"
            }
        ],
        "medications": [
            {
                "id": "MED-001",
                "name": "Losartán",
                "dose": "50mg",
                "frequency": "1 vez al día",
                "prescribed_date": "2024-11-20"
            }
        ],
        "diagnoses": [
            {
                "id": "DIAG-001",
                "code": "I10",
                "description": "Hipertensión arterial esencial",
                "date": "2024-11-20"
            }
        ]
    }

def search_similar_chunks_mock(patient_id: int, question: str):
    """MOCK de Persona 3 - Por ahora retorna vacío"""
    # TODO: Implementar cuando Persona 3 termine
    return []

def build_context_from_records(patient_info: Dict, clinical_records: Dict, similar_chunks: List) -> str:
    """Construye el contexto (Persona 4 adaptado)"""
    
    context = f"""### INFORMACIÓN BÁSICA DEL PACIENTE
Nombre: {patient_info['name']}
Edad: {patient_info['age']} años
Documento: {patient_info['document_number']}

"""
    
    # Agregar citas
    if clinical_records.get('appointments'):
        context += "### CITAS MÉDICAS RECIENTES\n"
        for apt in clinical_records['appointments']:
            context += f"""- Fecha: {apt['date']}
  Médico: {apt['doctor']}
  Diagnóstico: {apt['diagnosis']}
  Notas: {apt.get('notes', 'Sin notas')}

"""
    
    # Agregar medicamentos
    if clinical_records.get('medications'):
        context += "### MEDICAMENTOS ACTUALES\n"
        for med in clinical_records['medications']:
            context += f"- {med['name']} {med['dose']} - {med['frequency']}\n"
        context += "\n"
    
    # Agregar diagnósticos
    if clinical_records.get('diagnoses'):
        context += "### DIAGNÓSTICOS\n"
        for diag in clinical_records['diagnoses']:
            context += f"- {diag['description']} (Código: {diag['code']}) - {diag['date']}\n"
        context += "\n"
    
    # Agregar chunks de vector search si existen
    if similar_chunks:
        context += "### INFORMACIÓN ADICIONAL RELEVANTE\n"
        for chunk in similar_chunks:
            context += f"- [Relevancia: {chunk.get('relevance_score', 0):.2f}] {chunk['text']}\n"
    
    return context

def build_sources(clinical_records: Dict, similar_chunks: List) -> List[Dict]:
    """Construye las fuentes"""
    sources = []
    
    for apt in clinical_records.get('appointments', []):
        sources.append({
            "type": "clinical_record",
            "source_id": apt['id'],
            "source_type": "appointment",
            "date": apt['date']
        })
    
    for chunk in similar_chunks:
        sources.append({
            "type": "vector_search",
            "source_type": chunk.get('source_type'),
            "relevance_score": chunk.get('relevance_score')
        })
    
    return sources

# === ENDPOINT PRINCIPAL ===

@router.post("/", response_model=QuerySuccess | QueryNoData | QueryError)
async def query_patient(input_data: QueryInput):
    """
    Endpoint principal para consultas RAG sobre datos clínicos.
    
    Flujo:
    1. Buscar paciente por documento (Persona 2)
    2. Obtener datos clínicos del paciente (Persona 2)
    3. Buscar fragmentos relevantes con vector search (Persona 3)
    4. Construir contexto (Persona 4)
    5. Consultar al LLM (Persona 5)
    6. Devolver respuesta estructurada
    """
    start_time = time.time()
    
    try:
        logger.info(f"📝 Query recibida: {input_data.question}")
        logger.info(f"👤 Documento: {input_data.document_type_id}-{input_data.document_number}")
        
        # === PASO 1: Buscar paciente (Persona 2) ===
        try:
            patient_info = get_patient_by_document_mock(
                input_data.document_type_id,
                input_data.document_number
            )
        except Exception as e:
            logger.error(f"❌ Paciente no encontrado: {e}")
            return QueryError(
                status="error",
                error={
                    "code": "PATIENT_NOT_FOUND",
                    "message": "No se encontró un paciente con el documento proporcionado",
                    "details": {"document_number": input_data.document_number}
                }
            )
        
        # === PASO 2: Obtener datos clínicos (Persona 2) ===
        clinical_records = get_clinical_records_mock(patient_info['patient_id'])
        
        # === PASO 3: Vector search (Persona 3) ===
        similar_chunks = search_similar_chunks_mock(
            patient_info['patient_id'],
            input_data.question
        )
        
        # === PASO 4: Construir contexto (Persona 4) ===
        context = build_context_from_records(
            patient_info,
            clinical_records,
            similar_chunks
        )
        
        logger.info(f"📄 Contexto construido: {len(context)} caracteres")
        
        # Verificar si hay datos suficientes
        if len(context.strip()) < 100:
            return QueryNoData(
                status="no_data",
                message="No se encontraron datos clínicos relevantes para el paciente",
                metadata={
                    "patient_id": patient_info['patient_id'],
                    "query_time_ms": int((time.time() - start_time) * 1000)
                }
            )
        
        # === PASO 5: Consultar al LLM (Persona 5) ===
        llm_response = await llm_service.run_llm(
            question=input_data.question,
            context=context
        )
        
        # Determinar status
        status = llm_service.determine_status(llm_response.text, context)
        
        if status == "no_data":
            return QueryNoData(
                status="no_data",
                message=llm_response.text,
                metadata={
                    "patient_id": patient_info['patient_id'],
                    "query_time_ms": int((time.time() - start_time) * 1000),
                    "model_used": llm_response.model_used
                }
            )
        
        # === PASO 6: Construir respuesta final ===
        sources = build_sources(clinical_records, similar_chunks)
        
        query_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "answer": {
                "text": llm_response.text,
                "confidence": llm_response.confidence,
                "model_used": llm_response.model_used
            },
            "sources": sources,
            "metadata": {
                "total_records_analyzed": len(clinical_records.get('appointments', [])) + 
                                         len(clinical_records.get('medications', [])) +
                                         len(similar_chunks),
                "query_time_ms": query_time_ms,
                "sources_used": len(sources),
                "context_tokens": len(context.split()),
                "model_used": llm_response.model_used,
                "tokens_used": llm_response.tokens_used
            }
        }
        
        logger.info(f"✅ Query completada en {query_time_ms}ms")
        
        return QuerySuccess(
            status="success",
            data=response_data
        )
    
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        return QueryError(
            status="error",
            error={
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
                "details": {"error": str(e)}
            }
        )