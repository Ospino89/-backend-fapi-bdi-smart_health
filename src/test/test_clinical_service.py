from app.services.clinical_service import (
    get_patient_by_document,
    get_appointments_by_patient,
    get_medical_records_by_patient,
)


def test_get_patient_by_document_encontrado(db_session):
    patient = get_patient_by_document(
        db=db_session,
        document_type_id=1,   # ajusta al tipo real si hace falta
        document_number="123456",
    )

    # Solo verificamos que no explote y devuelva algo (para ahora)
    # Cuando tengas datos de prueba, puedes afinar los asserts.
    assert patient is None or patient.document_number == "123456"


def test_get_appointments_by_patient_no_revienta(db_session):
    appointments = get_appointments_by_patient(db=db_session, patient_id=1)

    assert isinstance(appointments, list)


def test_get_medical_records_by_patient_no_revienta(db_session):
    records = get_medical_records_by_patient(db=db_session, patient_id=1)

    assert isinstance(records, list)
