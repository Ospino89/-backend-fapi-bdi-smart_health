# Formato de salida de Vector Search
# La función search_similar_chunks(patient_id, question, k) devuelve una lista de objetos con la forma:
# chunk_text: str → texto relevante (motivo, diagnóstico, resumen, etc.).

# source_type: str → de dónde viene ("appointment", "diagnosis", "medical_record", "medication").

# source_id: int → id de la fila en su tabla.

# patient_id: int → id del paciente dueño de ese dato.

# date: datetime | null → fecha asociada al dato (cita, diagnóstico, etc.).

# relevance_score: float → score de relevancia (más alto = más relevante).