from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PatientDao:
    patient_id: int
    creator: int
    date_created: datetime
    changed_by: Optional[int]
    date_changed: Optional[datetime]
    voided: bool
    voided_by: Optional[int]
    date_voided: Optional[datetime]
    void_reason: Optional[str]
    allergy_status: str
