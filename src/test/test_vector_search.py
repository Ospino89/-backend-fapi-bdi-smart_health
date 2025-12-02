import asyncio

from app.services.vector_search import search_similar_chunks


def test_search_similar_chunks_sin_resultados(db_session):
    """
    T_P3_001 – No hay chunks similares para el paciente/pregunta.
    """
    # La función NO recibe db_session, solo (patient_id, question, k, min_score...)
    chunks = asyncio.run(
        search_similar_chunks(
            patient_id=9999,
            question="pregunta de prueba",
            k=5,
        )
    )

    assert isinstance(chunks, list)
    # Puede ser lista vacía o solo chunks de ese paciente
    assert len(chunks) == 0 or all(c.patient_id == 9999 for c in chunks)


def test_search_similar_chunks_con_limite_k(db_session):
    """
    T_P3_002 – Respeta el límite k de resultados.
    """
    chunks = asyncio.run(
        search_similar_chunks(
            patient_id=1,
            question="pregunta de prueba",
            k=3,
        )
    )

    assert isinstance(chunks, list)
    assert len(chunks) <= 3
