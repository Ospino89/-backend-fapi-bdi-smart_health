# src/app/services/rag_context.py
"""
P4 – Construcción de contexto, sources y metadata para el sistema RAG.
Este módulo recibe datos clínicos (P2) y fragmentos relevantes (P3)
y los transforma en:
- Un contexto en texto plano para el LLM (GPT-4o-mini).
- Una lista de fuentes estructuradas.
- Metadatos de rendimiento y trazabilidad.
"""

import tiktoken
from datetime import date
from typing import List, Dict, Any
from src.app.schemas.clinical import PatientInfo, ClinicalRecords
from src.app.schemas.rag import SimilarChunk

def calculate_age(birth_date: date) -> int:
    """Calcula la edad a partir de la fecha de nacimiento."""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def build_context(
    patient: PatientInfo,
    records: ClinicalRecords,
    similar_chunks: List[SimilarChunk],
    max_tokens: int = 4000
) -> tuple[str, int]:
    parts = []
    name_parts = [
        patient.first_name,
        patient.middle_name,
        patient.first_surname,
        patient.second_surname
    ]
    full_name = " ".join(part for part in name_parts if part is not None)
    age = calculate_age(patient.birth_date)

    parts.append("### Información Básica del Paciente")
    parts.append(f"Nombre: {full_name}")
    parts.append(f"Edad: {age} años")
    parts.append(f"Género: {patient.gender}")
    parts.append(f"Documento: {patient.document_number} (Tipo ID: {patient.document_type_id})")

    if records.appointments:
        parts.append("\n### Citas Médicas Recientes")
        sorted_appts = sorted(
            records.appointments,
            key=lambda x: (x.appointment_date, x.start_time or x.end_time or date.min),
            reverse=True
        )[:5]
        for appt in sorted_appts:
            time_str = f" a las {appt.start_time}" if appt.start_time else ""
            reason_str = f": {appt.reason}" if appt.reason else ""
            parts.append(f"- {appt.appointment_date}{time_str}{reason_str}")

    if records.diagnoses:
        parts.append("\n### Diagnósticos Registrados")
        for dx in records.diagnoses:
            desc = dx.description or f"Código CIE: {dx.icd_code or 'N/A'}"
            parts.append(f"- {desc}")

    if records.prescriptions:
        parts.append("\n### Medicamentos Recetados")
        for rx in records.prescriptions:
            if rx.instruction:
                parts.append(f"- {rx.instruction}")
            else:
                med_info = f"Medicamento ID {rx.medication_id}"
                if rx.dosage:
                    med_info += f", dosis: {rx.dosage}"
                parts.append(f"- {med_info}")

    if similar_chunks:
        parts.append("\n### Información Adicional Relevante")
        sorted_chunks = sorted(similar_chunks, key=lambda x: x.relevance_score, reverse=True)
        for chunk in sorted_chunks:
            parts.append(f"[Relevancia: {chunk.relevance_score:.2f}] {chunk.chunk_text}")
            date_str = f" ({chunk.date.strftime('%Y-%m-%d')})" if chunk.date else ""
            parts.append(f"[Fuente: {chunk.source_type} ID {chunk.source_id}{date_str}]")
            parts.append("")

    full_text = "\n".join(parts)
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(full_text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
        full_text = encoder.decode(tokens)

    return full_text, len(tokens)


def build_sources(
    similar_chunks: List[SimilarChunk],
    records: ClinicalRecords
) -> List[Dict[str, Any]]:
    sources = []
    for chunk in similar_chunks:
        sources.append({
            "type": "vector_search",
            "source_type": chunk.source_type,
            "source_id": chunk.source_id,
            "patient_id": chunk.patient_id,
            "relevance_score": round(chunk.relevance_score, 3),
            "text_snippet": chunk.chunk_text[:250]
        })
    for appt in records.appointments:
        sources.append({
            "type": "clinical_record",
            "source_type": "appointment",
            "appointment_id": appt.appointment_id,
            "date": appt.appointment_date.isoformat(),
            "text_snippet": (appt.reason or "")[:250]
        })
    return sources


def build_metadata(
    records: ClinicalRecords,
    similar_chunks: List[SimilarChunk],
    query_time_sec: float,
    context_tokens: int
) -> Dict[str, Any]:
    total_clinical = (
        len(records.appointments) +
        len(records.medical_records) +
        len(records.prescriptions) +
        len(records.diagnoses)
    )
    return {
        "total_records_analyzed": total_clinical,
        "vector_chunks_retrieved": len(similar_chunks),
        "query_time_ms": round(query_time_sec * 1000, 2),
        "context_tokens": context_tokens,
        "sources_used": len(similar_chunks) + len(records.appointments)
    }