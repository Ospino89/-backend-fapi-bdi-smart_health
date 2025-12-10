# src/app/services/llm_service.py

import os
import logging
from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class LLMResponse(BaseModel):
    """Respuesta estructurada del LLM."""
    text: str
    confidence: float = 0.85
    model_used: str = "gpt-4"
    tokens_used: int = 0


class LLMService:
    """Servicio para interactuar con OpenAI GPT API."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en .env")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        self.max_tokens = 2000
        
        logger.info(f"LLM Service inicializado. Modelo: {self.model}")

    async def run_llm(
        self,
        question: str,
        context: str,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Genera una respuesta usando el modelo del LLM según el contexto clínico entregado.
        """
        
        if max_tokens is None:
            max_tokens = self.max_tokens

        system_prompt = (
            "Eres un asistente médico amigable y profesional.\n"
            "Respondes en un tono conversacional, como en un chat, sin usar símbolos de Markdown como ### o **.\n\n"
            "INSTRUCCIONES:\n"
            "1. Responde ÚNICAMENTE con la información del contexto clínico proporcionado.\n"
            "2. Si no tienes información, di 'No tengo esa información en el historial'.\n"
            "3. Usa un lenguaje claro y natural, como si hablaras con un colega.\n"
            "4. Organiza la información de forma cronológica cuando sea relevante.\n"
            "5. Menciona fechas, medicamentos y diagnósticos de forma natural en el texto.\n"
            "6. NO uses:\n"
            "   - Símbolos ### para títulos\n"
            "   - Asteriscos ** para negritas\n"
            "   - Guiones - para viñetas\n"
            "7. En lugar de listas con viñetas, escribe párrafos fluidos.\n"
            "8. Separa ideas con saltos de línea simples para mejor legibilidad.\n\n"
            "EJEMPLO DE ESTILO:\n"
            "Según el historial clínico, el paciente tuvo una cita el 2 de marzo de 2022 para control de presión arterial con la doctora Camila Cárdenas.\n\n"
            "El 10 de octubre de 2022 acudió a emergencia por síntomas respiratorios.\n\n"
            "La más reciente fue el 9 de noviembre de 2024, un examen médico de chequeo general con la doctora Carolina Gutiérrez, especialista en medicina física y rehabilitación.\n"
        )

        user_message = (
            f"CONTEXTO CLÍNICO:\n{context}\n\n"
            f"PREGUNTA DEL USUARIO:\n{question}\n\n"
            "Responde únicamente con la información del contexto."
        )

        try:
            logger.info("Llamando a la API de OpenAI.")
            logger.debug(f"Longitud del contexto: {len(context)} caracteres.")

            response = await self.client.chat.completions.create(
                model=self.model,
                max_completion_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
            )

            if not response.choices:
                raise ValueError("La API retornó una respuesta vacía.")

            response_text = response.choices[0].message.content

            if not isinstance(response_text, str) or len(response_text.strip()) < 10:
                raise ValueError("La respuesta generada no es válida.")

            tokens_used = 0
            if hasattr(response, "usage") and response.usage is not None:
                tokens_used = getattr(response.usage, "completion_tokens", 0)

            logger.info(f"Respuesta del LLM recibida. Tokens usados: {tokens_used}")

            return LLMResponse(
                text=response_text.strip(),
                confidence=0.85,
                model_used=self.model,
                tokens_used=tokens_used
            )

        except Exception as e:
            logger.error(f"Error en la llamada al LLM: {type(e).__name__}: {str(e)}")
            raise


# Singleton global
llm_service = LLMService()