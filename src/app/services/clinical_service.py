# src/app/services/clinical_service.py
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
import logging

# Modelos SQLAlchemy
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription
from app.models.diagnosis import Diagnosis
from app.models.record_diagnosis import RecordDiagnosis

# Schemas Pydantic
from app.schemas.clinical import (
    PatientInfo,
    AppointmentDTO,
    MedicalRecordDTO,
    PrescriptionDTO,
    DiagnosisDTO,
    ClinicalRecords,
    ClinicalDataResult
)

logger = logging.getLogger(__name__)

# ============================================================================ 
# P2-2: Función para obtener paciente por documento
# ============================================================================

def get_patient_by_document(
    db: Session,
    document_type_id: int,
    document_number: str
) -> Optional[PatientInfo]:
    """
    Busca paciente por document_type_id y document_number.
    Devuelve PatientInfo si existe, o None si no se encuentra.
    """
    try:
        patient = (
            db.query(Patient)
            .filter(
                Patient.document_type_id == document_type_id,
                Patient.document_number == document_number
            )
            .one_or_none()
        )
    except Exception:
        logger.exception("Error ejecutando query get_patient_by_document")
        raise

    if not patient:
        return None

    # Mapear a Pydantic usando orm_mode
    return PatientInfo.from_orm(patient)


# ============================================================================ 
# P2-3: Funciones para obtener datos clínicos por paciente
# ============================================================================

def get_appointments_by_patient(db: Session, patient_id: int) -> List[AppointmentDTO]:
    """
    Obtiene todas las citas de un paciente, ordenadas por fecha descendente.
    """
    try:
        appointments = (
            db.query(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .order_by(Appointment.appointment_date.desc())
            .all()
        )
    except Exception:
        logger.exception("Error ejecutando query get_appointments_by_patient")
        raise

    # Convertir objetos SQLAlchemy a DTOs Pydantic
    return [AppointmentDTO.from_orm(apt) for apt in appointments]


def get_medical_records_by_patient(db: Session, patient_id: int) -> List[MedicalRecordDTO]:
    """
    Obtiene todos los registros médicos de un paciente, ordenados por fecha descendente.
    """
    try:
        records = (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.registration_datetime.desc())
            .all()
        )
    except Exception:
        logger.exception("Error ejecutando query get_medical_records_by_patient")
        raise

    return [MedicalRecordDTO.from_orm(rec) for rec in records]


def get_prescriptions_by_patient(db: Session, patient_id: int) -> List[PrescriptionDTO]:
    """
    Obtiene todas las prescripciones de un paciente (a través de medical_records).
    """
    try:
        prescriptions = (
            db.query(Prescription)
            .join(
                MedicalRecord,
                Prescription.medical_record_id == MedicalRecord.medical_record_id
            )
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(Prescription.prescription_date.desc())
            .all()
        )
    except Exception:
        logger.exception("Error ejecutando query get_prescriptions_by_patient")
        raise

    return [PrescriptionDTO.from_orm(presc) for presc in prescriptions]


def get_diagnoses_by_patient(db: Session, patient_id: int) -> List[DiagnosisDTO]:
    """
    Obtiene todos los diagnósticos de un paciente (a través de record_diagnoses).
    Como es un JOIN de dos tablas, se mapea manualmente.
    """
    try:
        results = (
            db.query(Diagnosis, RecordDiagnosis)
            .join(
                RecordDiagnosis,
                Diagnosis.diagnosis_id == RecordDiagnosis.diagnosis_id
            )
            .join(
                MedicalRecord,
                RecordDiagnosis.medical_record_id == MedicalRecord.medical_record_id
            )
            .filter(MedicalRecord.patient_id == patient_id)
            .all()
        )
    except Exception:
        logger.exception("Error ejecutando query get_diagnoses_by_patient")
        raise

    # Mapear manualmente porque no es un objeto ORM directo
    diagnoses: List[DiagnosisDTO] = []
    for diag, rd in results:
        diagnoses.append(DiagnosisDTO(
            record_diagnosis_id=rd.record_diagnosis_id,
            diagnosis_id=diag.diagnosis_id,
            icd_code=diag.icd_code,
            description=diag.description,
            diagnosis_type=rd.diagnosis_type,
            note=rd.note
        ))

    return diagnoses


# ============================================================================ 
# Función principal que integra todo (usada por P1)
# ============================================================================

def fetch_patient_and_records(
    db: Session,
    document_type_id: int,
    document_number: str
) -> Tuple[Optional[PatientInfo], ClinicalDataResult]:
    """
    Función principal que obtiene paciente + todos sus registros clínicos.

    Returns:
        Tupla con:
        - PatientInfo o None (si no existe el paciente)
        - ClinicalDataResult con todos los registros y flag has_data
    """
    # 1. Buscar paciente
    patient = get_patient_by_document(db, document_type_id, document_number)

    if not patient:
        # Paciente no encontrado
        return None, ClinicalDataResult(
            patient=None,
            records=ClinicalRecords(),
            has_data=False
        )

    # 2. Obtener todos los registros clínicos
    appointments = get_appointments_by_patient(db, patient.patient_id)
    medical_records = get_medical_records_by_patient(db, patient.patient_id)
    prescriptions = get_prescriptions_by_patient(db, patient.patient_id)
    diagnoses = get_diagnoses_by_patient(db, patient.patient_id)

    # 3. Agrupar en ClinicalRecords
    records = ClinicalRecords(
        appointments=appointments,
        medical_records=medical_records,
        prescriptions=prescriptions,
        diagnoses=diagnoses
    )

    # 4. Determinar si hay datos (P2-5)
    has_data = any([
        len(appointments) > 0,
        len(medical_records) > 0,
        len(prescriptions) > 0,
        len(diagnoses) > 0
    ])

    # 5. Retornar resultado completo
    return patient, ClinicalDataResult(
        patient=patient,
        records=records,
        has_data=has_data
    )