import asyncio

from app.services.llm_client import get_embedding, EMBEDDING_DIM


def test_get_embedding_formato_basico():
    text = "hola mundo"

    embedding = asyncio.run(get_embedding(text))

    assert isinstance(embedding, str)
    assert embedding.startswith("[") and embedding.endswith("]")
    assert embedding.count("0") >= EMBEDDING_DIM
