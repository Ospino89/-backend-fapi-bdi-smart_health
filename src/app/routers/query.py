# src/app/routers/query.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Union
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import time
import asyncio

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


# === FUNCIONES AUXILIARES ===

def build_context_from_real_data(
    patient_info: PatientInfo,
    clinical_records: ClinicalRecords,
    similar_chunks: List
) -> str:
    """Construye el contexto clínico de manera segura"""
    
    from datetime import date, datetime

    # === Calcular edad ===
    age = "No disponible"
    if patient_info.birth_date:
        try:
            birth_date = (
                patient_info.birth_date
                if isinstance(patient_info.birth_date, date)
                else datetime.strptime(patient_info.birth_date, "%Y-%m-%d").date()
            )
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
        except Exception as e:
            logger.warning(f"Error calculando edad: {e}")
            age = "No disponible"

    # Usar getattr para todos los campos de patient_info
    first_name = getattr(patient_info, 'first_name', 'Nombre')
    first_surname = getattr(patient_info, 'first_surname', 'Apellido')
    document_number = getattr(patient_info, 'document_number', 'No disponible')
    gender = getattr(patient_info, 'gender', None) or "No registrado"
    email = getattr(patient_info, 'email', None) or "No registrado"

    context = f"""
### INFORMACIÓN BÁSICA DEL PACIENTE
Nombre: {first_name} {first_surname}
Edad: {age}
Documento: {document_number}
Género: {gender}
Email: {email}

"""

    # === CITAS ===
    if clinical_records.appointments:
        context += "### CITAS MÉDICAS RECIENTES\n"
        for apt in clinical_records.appointments[:10]:
            apt_date = getattr(apt, 'appointment_date', 'Fecha no disponible')
            apt_status = getattr(apt, 'status', None) or 'No disponible'
            apt_reason = getattr(apt, 'reason', None) or 'No especificado'
            
            context += f"""- Fecha: {apt_date}
  Estado: {apt_status}
  Motivo: {apt_reason}

"""

    # === REGISTROS MÉDICOS ===
    if clinical_records.medical_records:
        context += "### REGISTROS MÉDICOS\n"
        for rec in clinical_records.medical_records[:10]:
            desc = (
                getattr(rec, "summary_text", None) or
                getattr(rec, "description", None) or
                getattr(rec, "details", None) or
                getattr(rec, "notes", None) or
                "Sin descripción"
            )
            
            rec_date = getattr(rec, 'registration_datetime', 'Fecha no disponible')
            rec_type = getattr(rec, 'record_type', 'Tipo no especificado')

            context += (
                f"- Fecha: {rec_date}\n"
                f"  Tipo: {rec_type}\n"
                f"  Descripción: {desc}\n\n"
            )

    # === PRESCRIPCIONES ===
    if clinical_records.prescriptions:
        context += "### MEDICAMENTOS Y PRESCRIPCIONES\n"
        for presc in clinical_records.prescriptions[:15]:
            medication = getattr(presc, 'medication_name', 'Medicamento sin nombre')
            dosage = getattr(presc, 'dosage', '')
            frequency = getattr(presc, 'frequency', '')
            duration = getattr(presc, 'duration', None) or "Sin duración"
            notes = getattr(presc, 'notes', None) or "Sin notas"
            
            context += f"- {medication}: {dosage} - {frequency}\n"
            context += f"  Duración: {duration}\n"
            context += f"  Notas: {notes}\n"
        context += "\n"

    # === DIAGNÓSTICOS ===
    if clinical_records.diagnoses:
        context += "### DIAGNÓSTICOS\n"
        for diag in clinical_records.diagnoses[:15]:
            diag_desc = getattr(diag, 'description', 'Diagnóstico sin descripción')
            icd_code = getattr(diag, 'icd_code', 'Sin código')
            diag_type = getattr(diag, 'diagnosis_type', 'Tipo no especificado')
            note = getattr(diag, 'note', None) or "Sin nota"
            
            context += f"- {diag_desc} (Código ICD: {icd_code})\n"
            context += f"  Tipo: {diag_type}\n"
            context += f"  Nota: {note}\n"
        context += "\n"

    # === VECTOR SEARCH ===
    if similar_chunks:
        context += "### INFORMACIÓN ADICIONAL RELEVANTE (BÚSQUEDA SEMÁNTICA)\n"
        for chunk in similar_chunks[:5]:
            chunk_text = getattr(chunk, 'chunk_text', 'Texto no disponible')
            relevance = getattr(chunk, 'relevance_score', 0.0)
            source_type = getattr(chunk, 'source_type', 'Desconocida')
            chunk_date = getattr(chunk, 'date', 'Sin fecha')
            
            context += f"- [Relevancia: {relevance:.2f}] {chunk_text}\n"
            context += f"  Fuente: {source_type} - Fecha: {chunk_date}\n\n"

    return context


def build_sources_from_real_data(
    clinical_records: ClinicalRecords, 
    similar_chunks: List,
    sequence_counter: int
) -> List[Dict]:
    """
    Construye lista de fuentes siguiendo el formato de la especificación.
    Cada fuente tiene: source_id, type, relevance_score, y datos específicos.
    """
    sources = []
    current_sequence = sequence_counter

    # CITAS - formato especificación
    try:
        for apt in clinical_records.appointments[:5]:
            apt_id = getattr(apt, 'appointment_id', None)
            if not apt_id:
                continue
                
            apt_date = getattr(apt, 'appointment_date', None)
            apt_reason = getattr(apt, 'reason', None)
            
            # Intentar extraer información del doctor si existe
            doctor_name = getattr(apt, 'doctor_name', None)
            specialty = getattr(apt, 'specialty', None)
            
            source = {
                "source_id": current_sequence,
                "type": "appointment",
                "appointment_id": int(apt_id),
                "date": str(apt_date) if apt_date else None,
                "relevance_score": 0.95  # Alta relevancia para datos directos
            }
            
            # Agregar doctor si existe
            if doctor_name or specialty:
                source["doctor"] = {
                    "name": doctor_name or "No especificado",
                    "specialty": specialty or "No especificada"
                }
            
            if apt_reason:
                source["reason"] = apt_reason
                
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de appointments: {e}")

    # DIAGNÓSTICOS - formato especificación
    try:
        for diag in clinical_records.diagnoses[:5]:
            diag_id = getattr(diag, 'diagnosis_id', None)
            if not diag_id:
                continue
                
            diag_desc = getattr(diag, 'description', 'Sin descripción')
            icd_code = getattr(diag, 'icd_code', None)
            diag_date = getattr(diag, 'diagnosis_date', None)
            
            source = {
                "source_id": current_sequence,
                "type": "diagnosis",
                "diagnosis_id": int(diag_id),
                "description": diag_desc,
                "relevance_score": 0.92
            }
            
            if icd_code:
                source["icd_code"] = icd_code
            if diag_date:
                source["date"] = str(diag_date)
                
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de diagnoses: {e}")

    # PRESCRIPCIONES
    try:
        for presc in clinical_records.prescriptions[:3]:
            presc_id = getattr(presc, 'prescription_id', None)
            if not presc_id:
                continue
                
            medication = getattr(presc, 'medication_name', 'Sin nombre')
            presc_date = getattr(presc, 'prescription_date', None)
            
            source = {
                "source_id": current_sequence,
                "type": "prescription",
                "prescription_id": int(presc_id),
                "medication": medication,
                "date": str(presc_date) if presc_date else None,
                "relevance_score": 0.88
            }
            
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de prescriptions: {e}")

    # VECTOR CHUNKS
    try:
        for chunk in similar_chunks[:5]:
            source_id = getattr(chunk, 'source_id', None)
            if not source_id:
                continue
                
            source_type = getattr(chunk, 'source_type', 'unknown')
            relevance = getattr(chunk, 'relevance_score', 0.0)
            chunk_date = getattr(chunk, 'date', None)
            
            source = {
                "source_id": current_sequence,
                "type": "vector_search",
                "original_source_id": str(source_id),
                "source_type": source_type,
                "relevance_score": float(relevance),
                "date": str(chunk_date) if chunk_date else None
            }
            
            sources.append(source)
            current_sequence += 1
            
    except Exception as e:
        logger.warning(f"Error construyendo sources de vector chunks: {e}")

    return sources


def get_document_type_name(document_type_id: int) -> str:
    """Mapea ID de tipo de documento a nombre"""
    types = {
        1: "CC",  # Cédula de Ciudadanía
        2: "CE",  # Cédula de Extranjería
        3: "TI",  # Tarjeta de Identidad
        4: "PA",  # Pasaporte
        5: "RC",  # Registro Civil
        6: "MS",  # Menor sin identificación
        7: "AS",  # Adulto sin identificación
        8: "CD",  # Carné Diplomático
    }
    return types.get(document_type_id, "CC")


def _generate_fallback_response(clinical_records: ClinicalRecords, question: str) -> str:
    """
    Genera una respuesta básica cuando el LLM falla.
    Extrae información directamente de los registros clínicos.
    """
    response_parts = []
    
    # Analizar citas
    if clinical_records.appointments:
        response_parts.append("*Citas Médicas Recientes:*\n")
        for apt in clinical_records.appointments[:3]:
            date = getattr(apt, 'appointment_date', 'Fecha no disponible')
            reason = getattr(apt, 'reason', 'No especificado')
            status = getattr(apt, 'status', 'No disponible')
            response_parts.append(f"- {date}: {reason} (Estado: {status})")
    
    # Analizar diagnósticos
    if clinical_records.diagnoses:
        response_parts.append("\n*Diagnósticos:*\n")
        for diag in clinical_records.diagnoses[:3]:
            desc = getattr(diag, 'description', 'Sin descripción')
            icd = getattr(diag, 'icd_code', '')
            response_parts.append(f"- {desc} (ICD: {icd})")
    
    # Analizar prescripciones
    if clinical_records.prescriptions:
        response_parts.append("\n*Medicamentos Prescritos:*\n")
        for presc in clinical_records.prescriptions[:3]:
            med = getattr(presc, 'medication_name', 'Medicamento no especificado')
            dosage = getattr(presc, 'dosage', '')
            response_parts.append(f"- {med} {dosage}")
    
    if not response_parts:
        return "No se encontró información relevante para responder la pregunta."
    
    # Agregar nota sobre modo fallback
    response_parts.append("\n*Nota: Esta respuesta fue generada directamente desde los registros clínicos debido a un problema temporal con el asistente inteligente.*")
    
    return "\n".join(response_parts)


# === ENDPOINT PRINCIPAL ===

@router.post("/")
async def query_patient(input_data: QueryInput, db: Session = Depends(get_db)):
    """
    Endpoint principal de consulta RAG.
    Retorna formato según especificación del proyecto.
    """
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Mantener sequence_chat_id simple por ahora (puede venir del frontend después)
    sequence_chat_id = 1

    try:
        logger.info(f"📝 Pregunta: {input_data.question}")
        logger.info(f"👤 Documento: {input_data.document_type_id}-{input_data.document_number}")

        # 1. BUSCAR PACIENTE
        try:
            patient_info, clinical_data = fetch_patient_and_records(
                db=db,
                document_type_id=input_data.document_type_id,
                document_number=input_data.document_number
            )
        except Exception as e:
            logger.error(f"Error buscando paciente: {e}")
            return {
                "status": "error",
                "session_id": input_data.session_id,
                "sequence_chat_id": sequence_chat_id,
                "timestamp": timestamp,
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "Error al buscar datos del paciente",
                    "details": str(e)
                }
            }

        if not patient_info:
            doc_type = get_document_type_name(input_data.document_type_id)
            return {
                "status": "error",
                "session_id": input_data.session_id,
                "sequence_chat_id": sequence_chat_id,
                "timestamp": timestamp,
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": f"No se encontró paciente con documento {doc_type} {input_data.document_number}",
                    "details": "Verifique el tipo y número de documento"
                }
            }

        # 2. VECTOR SEARCH (sin fallar si hay error)
        similar_chunks = []
        try:
            similar_chunks = await search_similar_chunks(
                patient_id=getattr(patient_info, 'patient_id', None),
                question=input_data.question,
                k=15,
                min_score=0.3
            )
        except Exception as e:
            logger.warning(f"Vector search falló (continuando sin él): {e}")
            similar_chunks = []

        # 3. CONSTRUIR CONTEXTO
        try:
            context = build_context_from_real_data(
                patient_info=patient_info,
                clinical_records=clinical_data.records,
                similar_chunks=similar_chunks
            )
        except Exception as e:
            logger.error(f"Error construyendo contexto: {e}")
            return {
                "status": "error",
                "session_id": input_data.session_id,
                "sequence_chat_id": sequence_chat_id,
                "timestamp": timestamp,
                "error": {
                    "code": "CONTEXT_BUILD_ERROR",
                    "message": "Error al construir contexto clínico",
                    "details": str(e)
                }
            }

        # Extraer info del paciente de manera segura
        patient_id = getattr(patient_info, 'patient_id', None)
        first_name = getattr(patient_info, 'first_name', 'Nombre')
        first_surname = getattr(patient_info, 'first_surname', 'Apellido')
        second_surname = getattr(patient_info, 'second_surname', '')
        document_number = getattr(patient_info, 'document_number', 'No disponible')
        doc_type = get_document_type_name(input_data.document_type_id)
        
        full_name = f"{first_name} {first_surname}"
        if second_surname:
            full_name += f" {second_surname}"

        # 4. VERIFICAR SI HAY DATOS (Caso: sin datos)
        total_records = (
            len(clinical_data.records.appointments) +
            len(clinical_data.records.medical_records) +
            len(clinical_data.records.prescriptions) +
            len(clinical_data.records.diagnoses) +
            len(similar_chunks)
        )

        if total_records == 0:
            return {
                "status": "success",
                "session_id": input_data.session_id,
                "sequence_chat_id": sequence_chat_id,
                "timestamp": timestamp,
                "patient_info": {
                    "patient_id": patient_id,
                    "full_name": full_name,
                    "document_type": doc_type,
                    "document_number": document_number
                },
                "answer": {
                    "text": f"El paciente {full_name} no tiene registros clínicos en el sistema.",
                    "confidence": 1.0,
                    "model_used": "system"
                },
                "sources": [],
                "metadata": {
                    "total_records_analyzed": 0,
                    "query_time_ms": int((time.time() - start_time) * 1000),
                    "sources_used": 0
                }
            }

        # 5. LLAMAR AL LLM (con retry y fallback)
        llm_response = None
        llm_attempts = 0
        max_attempts = 2
        
        while llm_attempts < max_attempts and not llm_response:
            llm_attempts += 1
            try:
                logger.info(f"Intento {llm_attempts}/{max_attempts} de llamada al LLM")
                
                llm_response = await llm_service.run_llm(
                    question=input_data.question,
                    context=context
                )
                
                # Validación adicional
                if not llm_response or not hasattr(llm_response, 'text') or not llm_response.text:
                    if llm_attempts < max_attempts:
                        logger.warning(f"Respuesta LLM inválida, reintentando...")
                        await asyncio.sleep(0.5)  # Pequeña pausa antes de reintentar
                        continue
                    else:
                        raise ValueError("Respuesta del LLM vacía después de múltiples intentos")
                
                # Validar que la respuesta tenga contenido útil
                if len(llm_response.text.strip()) < 10:
                    if llm_attempts < max_attempts:
                        logger.warning(f"Respuesta LLM muy corta, reintentando...")
                        await asyncio.sleep(0.5)
                        continue
                    else:
                        raise ValueError("Respuesta del LLM demasiado corta")
                
                # Si llegamos aquí, tenemos una respuesta válida
                break
                
            except Exception as e:
                logger.error(f"Error en intento {llm_attempts} del LLM: {e}")
                
                if llm_attempts >= max_attempts:
                    # Último intento falló, generar respuesta de fallback
                    logger.warning("Usando respuesta de fallback debido a fallo del LLM")
                    
                    # Construir respuesta básica desde el contexto
                    fallback_text = _generate_fallback_response(
                        clinical_data.records,
                        input_data.question
                    )
                    
                    return {
                        "status": "success",
                        "session_id": input_data.session_id,
                        "sequence_chat_id": sequence_chat_id,
                        "timestamp": timestamp,
                        "patient_info": {
                            "patient_id": patient_id,
                            "full_name": full_name,
                            "document_type": doc_type,
                            "document_number": document_number
                        },
                        "answer": {
                            "text": fallback_text,
                            "confidence": 0.65,  # Menor confianza para respuesta de fallback
                            "model_used": "fallback-system"
                        },
                        "sources": [],
                        "metadata": {
                            "total_records_analyzed": total_records,
                            "query_time_ms": int((time.time() - start_time) * 1000),
                            "sources_used": 0,
                            "context_tokens": 0,
                            "fallback_mode": True
                        }
                    }
                else:
                    # Aún quedan intentos
                    await asyncio.sleep(0.5)
                    continue

        # 6. CONSTRUIR SOURCES
        try:
            sources = build_sources_from_real_data(
                clinical_data.records, 
                similar_chunks,
                sequence_counter=1
            )
        except Exception as e:
            logger.warning(f"Error construyendo sources: {e}")
            sources = []

        # 7. RESPUESTA EXITOSA (formato especificación)
        response = {
            "status": "success",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": timestamp,
            "patient_info": {
                "patient_id": patient_id,
                "full_name": full_name,
                "document_type": doc_type,
                "document_number": document_number
            },
            "answer": {
                "text": llm_response.text,
                "confidence": getattr(llm_response, 'confidence', 0.85),
                "model_used": getattr(llm_response, 'model_used', 'unknown')
            },
            "sources": sources,
            "metadata": {
                "total_records_analyzed": total_records,
                "query_time_ms": int((time.time() - start_time) * 1000),
                "sources_used": len(sources),
                "context_tokens": getattr(llm_response, 'tokens_used', 0)
            }
        }

        logger.info(f"✅ Respuesta generada exitosamente en {response['metadata']['query_time_ms']}ms")
        return response

    except Exception as e:
        logger.exception("❌ Error inesperado en endpoint")
        return {
            "status": "error",
            "session_id": input_data.session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": timestamp,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
                "details": str(e)
            }
        }