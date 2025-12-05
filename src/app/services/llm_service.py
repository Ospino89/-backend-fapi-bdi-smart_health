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
            
            logger.info(f"🤖 Llamando al LLM. Contexto: {len(context)} chars")
            
            # Llamar al LLM
            response = await llm_client.generate(
                prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT
            )
            
            # Extraer texto de respuesta
            response_text = response.get('text', '').strip()
            
            logger.info(f"✅ LLM respondió. Longitud: {len(response_text)} chars")
            
            # Validar respuesta (más permisivo)
            if not LLMService._validate_response(response_text):
                logger.error(f"❌ Validación falló. Respuesta: '{response_text[:100]}...'")
                raise LLMError(
                    message="Respuesta del LLM inválida o incoherente",
                    details={
                        "response_length": len(response_text),
                        "response_preview": response_text[:200]
                    }
                )
            
            # Calcular confianza
            confidence = LLMService._calculate_confidence(
                response_text, 
                context
            )
            
            llm_response = LLMResponse(
                text=response_text,
                confidence=confidence,
                model_used=response.get('model_used', 'unknown'),
                tokens_used=response.get('tokens_used', 0)
            )
            
            logger.info(f"📊 Confidence: {confidence}, Tokens: {llm_response.tokens_used}")
            
            return llm_response
            
        except LLMError:
            raise
        except Exception as e:
            logger.exception(f"Error inesperado en run_llm")
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
            "sin información",
            "no dispongo"
        ]
        
        # Contexto muy corto
        if len(context.strip()) < 50:
            return 0.3
        
        # Respuesta indica falta de datos
        has_no_data_indicator = any(indicator in answer_lower for indicator in no_data_indicators)
        if has_no_data_indicator:
            return 0.4
        
        # Respuesta muy corta (pero válida)
        if len(answer) < 50:
            return 0.6
        
        # Respuesta robusta con buen contexto
        if len(answer) > 100 and len(context) > 200:
            return 0.92
        
        # Respuesta media con contexto medio
        if len(answer) > 50 and len(context) > 100:
            return 0.8
        
        # Caso promedio
        return 0.75
    
    @staticmethod
    def _validate_response(answer: str) -> bool:
        """
        Valida que la respuesta del LLM sea coherente (P5-5).
        VERSIÓN MEJORADA - Más permisiva pero segura.
        """
        # 1. Validación básica: no puede estar vacío
        if not answer or not isinstance(answer, str):
            logger.warning("Respuesta es None o no es string")
            return False
        
        answer_stripped = answer.strip()
        
        # 2. Debe tener al menos 5 caracteres
        if len(answer_stripped) < 5:
            logger.warning(f"Respuesta muy corta: {len(answer_stripped)} chars")
            return False
        
        # 3. Debe tener al menos 2 palabras
        words = answer_stripped.split()
        if len(words) < 2:
            logger.warning(f"Respuesta tiene menos de 2 palabras: {words}")
            return False
        
        # 4. Verificar que no sea solo caracteres repetidos (ej: "aaaaaaa")
        if len(set(answer_stripped.replace(' ', ''))) < 3:
            logger.warning("Respuesta parece tener caracteres repetidos")
            return False
        
        # 5. REMOVIDO: El chequeo de unique_ratio era demasiado estricto
        #    Respuestas médicas legítimas pueden tener muchas palabras repetidas
        #    como "paciente", "fecha", "diagnóstico", etc.
        
        # 6. Verificar que contenga al menos algunas letras
        has_letters = any(c.isalpha() for c in answer_stripped)
        if not has_letters:
            logger.warning("Respuesta no contiene letras")
            return False
        
        logger.debug(f"✅ Respuesta validada: {len(words)} palabras, {len(answer_stripped)} chars")
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
        
        NOTA: Este método ya no es usado en el flujo principal (query.py),
        pero se mantiene por compatibilidad.
        """
        no_data_indicators = [
            "no hay información",
            "no se encuentra",
            "no hay datos",
            "no disponible",
            "sin información",
            "no dispongo",
            "no se encontr",
            "no registr"
        ]
        
        answer_lower = answer_text.lower()
        
        # Contexto vacío o muy corto
        if len(context.strip()) < 20:
            return "no_data"
        
        # Respuesta indica falta de datos de forma prominente
        # (debe estar al inicio o aparecer múltiples veces)
        if any(indicator in answer_lower[:100] for indicator in no_data_indicators):
            return "no_data"
        
        return "success"


# Instancia global del servicio
llm_service = LLMService()