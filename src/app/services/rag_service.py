from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID
import json

from ..models.audit_logs import AuditLog

class RAGService:
    """
    Servicio que implementa el patrón RAG (Retrieval-Augmented Generation)
    """
    
    @staticmethod
    async def process_query(
        db: Session,
        user_id: int,
        session_id: UUID,
        document_type_id: int,
        document_number: str,
        question: str
    ) -> Dict:
        """
        Procesa una consulta RAG completa:
        1. Busca el paciente
        2. Recupera datos clínicos relevantes
        3. Realiza búsqueda vectorial (si aplica)
        4. Construye contexto para LLM
        5. Llama al LLM
        6. Registra auditoría
        """
        
        # PASO 1: Buscar paciente (debes tener una tabla de pacientes)
        patient = RAGService._find_patient(
            db, document_type_id, document_number
        )
        
        if not patient:
            raise ValueError(
                f"No se encontró paciente con documento tipo {document_type_id} número {document_number}"
            )
        
        # PASO 2: Recuperar datos clínicos del paciente
        clinical_data = RAGService._retrieve_clinical_data(
            db, patient["patient_id"]
        )
        
        # PASO 3: Vector search (si tienes embeddings configurados)
        # relevant_vectors = RAGService._vector_search(db, question, patient["patient_id"])
        
        # PASO 4: Construir contexto
        context = RAGService._build_context(clinical_data, question)
        
        # PASO 5: Llamar al LLM (Claude API)
        llm_response = await RAGService._call_llm(context, question)
        
        # PASO 6: Obtener sequence_chat_id
        sequence_chat_id = RAGService._get_next_sequence(db, session_id)
        
        # Construir respuesta en formato estándar
        response = {
            "status": "success",
            "session_id": session_id,
            "sequence_chat_id": sequence_chat_id,
            "timestamp": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
            "patient_info": {
                "patient_id": patient["patient_id"],
                "full_name": patient["full_name"],
                "document_type": patient["document_type"],
                "document_number": document_number
            },
            "answer": {
                "text": llm_response["text"],
                "confidence": llm_response.get("confidence", 0.85),
                "model_used": "claude-sonnet-4-5"
            },
            "sources": llm_response.get("sources", []),
            "metadata": {
                "total_records_analyzed": len(clinical_data),
                "query_time_ms": 0,  # Se calcula en el router
                "sources_used": len(llm_response.get("sources", [])),
                "context_tokens": llm_response.get("context_tokens")
            }
        }
        
        # PASO 7: Registrar auditoría
        RAGService._save_audit(
            db, user_id, session_id, sequence_chat_id,
            document_type_id, document_number, question, response
        )
        
        return response
    
    @staticmethod
    def _find_patient(db: Session, document_type_id: int, document_number: str) -> Optional[Dict]:
        """Busca un paciente por tipo y número de documento"""
        # DEBES IMPLEMENTAR: consulta a tu tabla de pacientes
        # Por ahora retorno datos de ejemplo
        return {
            "patient_id": 123,
            "full_name": "Juan Pérez García",
            "document_type": "CC",
            "document_number": document_number
        }
    
    @staticmethod
    def _retrieve_clinical_data(db: Session, patient_id: int) -> List[Dict]:
        """Recupera datos clínicos del paciente"""
        # DEBES IMPLEMENTAR: consultar tus tablas clínicas
        # Ejemplo: citas médicas, diagnósticos, tratamientos, etc.
        return []
    
    @staticmethod
    def _build_context(clinical_data: List[Dict], question: str) -> str:
        """Construye el contexto para el LLM"""
        if not clinical_data:
            return f"No hay datos clínicos disponibles para responder: {question}"
        
        context = "Información clínica del paciente:\n\n"
        for record in clinical_data:
            context += f"- {record}\n"
        
        return context
    
    @staticmethod
    async def _call_llm(context: str, question: str) -> Dict:
        """Llama al LLM (Claude API)"""
        # DEBES IMPLEMENTAR: llamada real a Claude API
        # Por ahora retorno respuesta de ejemplo
        return {
            "text": "Respuesta de ejemplo del LLM. Debes implementar la llamada real a Claude API.",
            "confidence": 0.90,
            "sources": [],
            "context_tokens": len(context.split())
        }
    
    @staticmethod
    def _get_next_sequence(db: Session, session_id: UUID) -> int:
        """Obtiene el siguiente número de secuencia para la sesión"""
        last_log = db.query(AuditLog).filter(
            AuditLog.session_id == session_id
        ).order_by(AuditLog.sequence_chat_id.desc()).first()
        
        return (last_log.sequence_chat_id + 1) if last_log else 1
    
    @staticmethod
    def _save_audit(
        db: Session, user_id: int, session_id: UUID,
        sequence_chat_id: int, document_type_id: int,
        document_number: str, question: str, response: Dict
    ):
        """Guarda el registro de auditoría"""
        audit_log = AuditLog(
            user_id=user_id,
            session_id=session_id,
            sequence_chat_id=sequence_chat_id,
            document_type_id=document_type_id,
            document_number=document_number,
            question=question,
            response_json=response
        )
        
        db.add(audit_log)
        db.commit()