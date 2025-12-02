# src/app/models/patient.py
from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector  # Requiere pgvector.sqlalchemy instalado

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"schema": "smart_health"}

    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    first_surname = Column(String)
    second_surname = Column(String, nullable=True)
    birth_date = Column(Date)
    gender = Column(String)
    email = Column(String, nullable=True)
    document_type_id = Column(Integer)
    document_number = Column(String)
    registration_date = Column(TIMESTAMP, nullable=True)
    active = Column(Boolean, nullable=True)
    blood_type = Column(String, nullable=True)

    # Embedding vector: ajustar dimensión a la usada en tu proyecto (1536)
    # fullname_embedding = Column(Vector(1536), nullable=True)