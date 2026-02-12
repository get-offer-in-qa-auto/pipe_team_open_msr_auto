from dataclasses import dataclass
from datetime import datetime


@dataclass
class PatientDao:
    patient_id: int
    creator: int
    date_created: datetime
    changed_by: int | None
    date_changed: datetime | None
    voided: bool
    voided_by: int | None
    date_voided: datetime | None
    void_reason: str | None
    allergy_status: str
