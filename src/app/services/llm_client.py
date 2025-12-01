from openai import AsyncOpenAI
from typing import Dict
import logging
import os
from app.database.db_config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """Cliente para interactuar con OpenAI GPT"""
    
    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        
        if not self.use_mock:
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
        # Si está en modo mock, usar el mock
        if self.use_mock:
            from app.services.llm_client_mock import llm_client_mock
            logger.info("🎭 Usando LLM MOCK (modo desarrollo)")
            return await llm_client_mock.generate(prompt, system_prompt)
        
        # Código normal de OpenAI
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result = {
                "text": response.choices[0].message.content,
                "model_used": response.model,
                "tokens_used": response.usage.total_tokens
            }
            
            logger.info(f"LLM generó respuesta. Tokens usados: {result['tokens_used']}")
            return result
            
        except Exception as e:
            logger.error(f"Error en LLM: {str(e)}")
            from app.schemas.llm_schemas import LLMError
            raise LLMError(
                message="Error al generar respuesta del LLM",
                details={"error": str(e), "model": self.model}
            )

# Instancia global del cliente
llm_client = LLMClient()