from pydantic import BaseModel


class Medication(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str | None = None
    instructions: str | None = None


class Prescription(BaseModel):
    patient_name: str
    patient_age: str | None = None
    doctor_name: str
    doctor_title: str | None = None
    hospital: str | None = None
    date: str
    medications: list[Medication]
    notes: str | None = None
