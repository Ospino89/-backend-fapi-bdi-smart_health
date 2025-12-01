# src/app/schemas/clinical.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, time

# ============================================================================ 
# DTOs individuales para cada tipo de dato clínico
# ============================================================================

class PatientInfo(BaseModel):
    patient_id: int
    first_name: str
    middle_name: Optional[str] = None
    first_surname: str
    second_surname: Optional[str] = None
    birth_date: date
    gender: str
    email: Optional[str] = None
    document_type_id: int
    document_number: str
    registration_date: Optional[datetime] = None
    active: Optional[bool] = None
    blood_type: Optional[str] = None

    model_config = {"from_attributes": True}


class AppointmentDTO(BaseModel):
    """DTO para citas médicas"""
    appointment_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    appointment_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    appointment_type: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    creation_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MedicalRecordDTO(BaseModel):
    """DTO para registros médicos"""
    medical_record_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    primary_diagnosis_id: Optional[int] = None
    registration_datetime: Optional[datetime] = None
    record_type: Optional[str] = None
    summary_text: Optional[str] = None
    vital_signs: Optional[str] = None  # Puede ser JSON en string

    model_config = {"from_attributes": True}


class PrescriptionDTO(BaseModel):
    """DTO para prescripciones"""
    prescription_id: int
    medical_record_id: int
    medication_id: int
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instruction: Optional[str] = None
    prescription_date: Optional[date] = None
    alert_generated: Optional[bool] = None

    model_config = {"from_attributes": True}


class DiagnosisDTO(BaseModel):
    """DTO para diagnósticos"""
    record_diagnosis_id: int
    diagnosis_id: int
    icd_code: Optional[str] = None
    description: Optional[str] = None
    diagnosis_type: Optional[str] = None
    note: Optional[str] = None

    model_config = {"from_attributes": True}


# ============================================================================ 
# Contenedor para todos los registros clínicos
# ============================================================================

class ClinicalRecords(BaseModel):
    """Agrupa todos los tipos de registros clínicos de un paciente"""
    appointments: List[AppointmentDTO] = Field(default_factory=list)
    medical_records: List[MedicalRecordDTO] = Field(default_factory=list)
    prescriptions: List[PrescriptionDTO] = Field(default_factory=list)
    diagnoses: List[DiagnosisDTO] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ============================================================================ 
# Resultado completo: paciente + registros + flag de datos
# ============================================================================

class ClinicalDataResult(BaseModel):
    """
    Resultado completo de la búsqueda de datos clínicos.
    Usado por P1 para determinar si hay datos o no.
    """
    patient: Optional[PatientInfo] = None
    records: ClinicalRecords = Field(default_factory=ClinicalRecords)
    has_data: bool  # True si hay al menos un registro en cualquier lista

    model_config = {"from_attributes": True}
