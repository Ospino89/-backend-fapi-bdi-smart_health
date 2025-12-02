# src/app/services/llm_client.py

from typing import List

EMBEDDING_DIM = 1536  # EJEMPLO: 1536, 1024, etc.


async def get_embedding(text: str) -> str:
    """
    Stub temporal de get_embedding para poder probar search_similar_chunks.
    Devuelve un vector de ceros con la dimensión correcta.

    Persona 5 lo reemplazará luego por la llamada real al modelo de embeddings.
    """
    zeros = ",".join("0" for _ in range(EMBEDDING_DIM))
    return f"[{zeros}]"