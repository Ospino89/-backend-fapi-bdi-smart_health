from datetime import date

from app.services.rag_context import (
    build_context,
    build_sources,
    build_metadata,
    PatientInfo,
    ClinicalRecords,
    SimilarChunk,
)


def make_patient() -> PatientInfo:
    return PatientInfo(
        patient_id=1,
        document_type_id=1,
        document_number="123456",
        first_name="Juan",
        middle_name="Pérez",
        first_surname="García",
        second_surname="Lopez",
        sex="M",
        age=30,
        birth_date=date(1995, 1, 1),
        gender="M",
    )


def make_records(with_data: bool) -> ClinicalRecords:
    if with_data:
        return ClinicalRecords(
            appointments=[
                {
                    "appointment_id": 10,
                    "patient_id": 1,
                    "reason": "Control",
                    "appointment_date": date(2025, 12, 1),
                }
            ],
            diagnoses=[
                {
                    "record_diagnosis_id": 1,
                    "diagnosis_id": 5,
                    "icd_code": "X01",
                    "description": "Diagnóstico de prueba",
                    "diagnosis_type": "primary",
                    "note": None,
                }
            ],
            medical_records=[],
            prescriptions=[],
        )
    return ClinicalRecords(
        appointments=[],
        diagnoses=[],
        medical_records=[],
        prescriptions=[],
    )


def make_chunks() -> list[SimilarChunk]:
    return [
        SimilarChunk(
            chunk_text="Texto relevante 1",
            source_type="appointment",
            source_id=10,
            patient_id=1,
            date=date(2025, 12, 1),
            relevance_score=0.9,
        )
    ]


def test_build_context_con_datos():
    patient = make_patient()
    records = make_records(with_data=True)
    chunks = make_chunks()

    context, token_count = build_context(patient, records, chunks)

    assert isinstance(context, str)
    assert isinstance(token_count, int)
    assert "Juan" in context
    assert "Control" in context
    assert "Texto relevante 1" in context


def test_build_context_sin_datos():
    patient = make_patient()
    records = make_records(with_data=False)
    chunks: list[SimilarChunk] = []

    context, token_count = build_context(patient, records, chunks)

    assert isinstance(context, str)
    assert isinstance(token_count, int)


def test_build_sources_estructura_basica():
    records = make_records(with_data=True)
    chunks = make_chunks()

    sources = build_sources(chunks, records)

    assert isinstance(sources, list)
    assert len(sources) > 0
    first = sources[0]
    assert first["type"] == "vector_search"
    assert "source_type" in first
    assert "source_id" in first
    assert "relevance_score" in first


def test_build_metadata_basico():
    records = make_records(with_data=True)
    chunks = make_chunks()
    context, token_count = build_context(make_patient(), records, chunks)

    # llamada solo por posición: (chunks, records, query_time_ms, context_tokens)
def test_build_metadata_basico():
    records = make_records(with_data=True)
    chunks = make_chunks()
    context, token_count = build_context(make_patient(), records, chunks)

    metadata = build_metadata(records, chunks, 120, token_count)

    assert isinstance(metadata, dict)
    # 120 segundos → 120000 ms
    assert metadata.get("query_time_ms") == 120000
    assert metadata.get("context_tokens") == token_count
    assert metadata.get("total_records_analyzed") >= 1


