from openai import AsyncOpenAI
from typing import Dict
import logging
from app.database.db_config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Cliente para interactuar con OpenAI GPT"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.llm_timeout
        )
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
    
    async def generate(self, prompt: str, system_prompt: str) -> Dict:
        """
        Genera respuesta del LLM.
        
        Args:
            prompt: Prompt del usuario con contexto
            system_prompt: Instrucciones del sistema
            
        Returns:
            Dict con 'text', 'model_used', 'tokens_used'
            
        Raises:
            LLMError: Si hay error en la generación
        """
        try:
            # Preparar parámetros base
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
            }
            
            # gpt-5-nano solo acepta temperature=1 (default)
            # Para otros modelos, usar el configurado
            if not self.model.startswith("gpt-5"):
                params["temperature"] = self.temperature
            
            # Usar el parámetro correcto según el modelo
            if self.model.startswith(("gpt-5", "gpt-4.1", "gpt-4o")):
                params["max_completion_tokens"] = self.max_tokens
            else:
                params["max_tokens"] = self.max_tokens
            
            response = await self.client.chat.completions.create(**params)
            
            result = {
                "text": response.choices[0].message.content,
                "model_used": response.model,
                "tokens_used": response.usage.total_tokens
            }
            
            logger.info(f"✅ LLM generó respuesta. Tokens usados: {result['tokens_used']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en LLM: {str(e)}")
            from app.schemas.llm_schemas import LLMError
            raise LLMError(
                message="Error al generar respuesta del LLM",
                details={"error": str(e), "model": self.model}
            )

# Instancia global del cliente
llm_client = LLMClient()