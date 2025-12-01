from typing import Literal
import logging
from app.services.llm_client import llm_client
from app.schemas.llm_schemas import LLMResponse, LLMError

logger = logging.getLogger(__name__)

# System Prompt (P5-3)
SYSTEM_PROMPT = """Eres un asistente médico especializado que responde preguntas sobre pacientes basándote ÚNICAMENTE en los datos clínicos proporcionados en el contexto.

REGLAS ESTRICTAS:
1. Solo usa información presente en el contexto proporcionado
2. Si no hay datos suficientes, indica claramente "No hay información disponible sobre [tema]"
3. No inventes ni asumas información que no esté en el contexto
4. Sé preciso, conciso y profesional
5. Cita las fuentes cuando sea relevante (por ejemplo: "Según cita del 15/03/2024...")

FORMATO DE RESPUESTA:
- Responde en español
- Usa lenguaje claro y profesional
- Estructura la información de forma organizada
- Si hay múltiples datos relevantes, organízalos por categorías
"""

def build_user_prompt(question: str, context: str) -> str:
    """Construye el prompt del usuario con la pregunta y el contexto."""
    return f"""CONTEXTO CLÍNICO DEL PACIENTE:
{context}

PREGUNTA DEL USUARIO:
{question}

Por favor, responde la pregunta basándote únicamente en el contexto proporcionado."""


class LLMService:
    """Servicio para ejecutar el LLM con contexto RAG"""
    
    @staticmethod
    async def run_llm(question: str, context: str) -> LLMResponse:
        """
        Ejecuta el LLM con la pregunta y contexto (P5-4).
        
        Args:
            question: Pregunta del usuario
            context: Contexto construido con datos del paciente
            
        Returns:
            LLMResponse con la respuesta generada
            
        Raises:
            LLMError: Si hay error en la generación
        """
        try:
            # Validar inputs
            if not context or len(context.strip()) < 10:
                logger.warning("Contexto vacío o muy corto")
                # Continuar de todas formas, el LLM responderá que no hay info
            
            # Construir el prompt
            user_prompt = build_user_prompt(question, context)
            
            # Llamar al LLM
            response = await llm_client.generate(
                prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT
            )
            
            # Validar respuesta
            if not LLMService._validate_response(response['text']):
                raise LLMError(
                    message="Respuesta del LLM inválida o incoherente",
                    details={"response_length": len(response['text'])}
                )
            
            # Calcular confianza
            confidence = LLMService._calculate_confidence(
                response['text'], 
                context
            )
            
            return LLMResponse(
                text=response['text'],
                confidence=confidence,
                model_used=response['model_used'],
                tokens_used=response.get('tokens_used', 0)
            )
            
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Error inesperado en run_llm: {str(e)}")
            raise LLMError(
                message="Error inesperado al ejecutar LLM",
                details={"error": str(e)}
            )
    
    @staticmethod
    def _calculate_confidence(answer: str, context: str) -> float:
        """
        Calcula nivel de confianza de la respuesta (P5-5).
        
        Criterios:
        - Contexto vacío o respuesta "sin datos" -> baja confianza
        - Respuesta larga y con contexto robusto -> alta confianza
        """
        answer_lower = answer.lower()
        
        # Indicadores de falta de datos
        no_data_indicators = [
            "no hay información",
            "no se encuentra",
            "no hay datos",
            "no disponible",
            "sin información"
        ]
        
        # Contexto muy corto
        if len(context.strip()) < 50:
            return 0.2
        
        # Respuesta indica falta de datos
        if any(indicator in answer_lower for indicator in no_data_indicators):
            return 0.3
        
        # Respuesta muy corta
        if len(answer) < 50:
            return 0.5
        
        # Respuesta robusta con buen contexto
        if len(answer) > 100 and len(context) > 200:
            return 0.9
        
        # Caso promedio
        return 0.7
    
    @staticmethod
    def _validate_response(answer: str) -> bool:
        """
        Valida que la respuesta del LLM sea coherente (P5-5).
        """
        if not answer or len(answer.strip()) < 10:
            return False
        
        # Verificar que no sea puro texto repetido
        words = answer.split()
        if len(words) < 3:
            return False
        
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.3:  # Menos del 30% de palabras únicas
            return False
        
        return True
    
    @staticmethod
    def determine_status(
        answer_text: str, 
        context: str
    ) -> Literal["success", "no_data"]:
        """
        Determina si el status debe ser 'success' o 'no_data' (P5-5).
        
        Reglas de negocio:
        - Si el contexto está vacío -> no_data
        - Si la respuesta indica falta de información -> no_data
        - En otro caso -> success
        """
        no_data_indicators = [
            "no hay información",
            "no se encuentra",
            "no hay datos",
            "no disponible",
            "sin información"
        ]
        
        answer_lower = answer_text.lower()
        
        # Contexto vacío o muy corto
        if len(context.strip()) < 20:
            return "no_data"
        
        # Respuesta indica falta de datos
        if any(indicator in answer_lower for indicator in no_data_indicators):
            return "no_data"
        
        return "success"


# Instancia global del servicio
llm_service = LLMService()