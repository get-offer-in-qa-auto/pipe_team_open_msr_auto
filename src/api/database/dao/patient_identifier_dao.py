import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatientIdentifierDao:
    patient_identifier_id: int
    patient_id: int
    identifier: str
    identifier_type: int
    preferred: int
    location_id: int
    creator: int
    date_created: datetime.datetime
    date_changed: Optional[datetime.datetime]
    changed_by: int
    voided: Optional[str]
    voided_by: Optional[int]
    date_voided: Optional[datetime.datetime]
    void_reason: Optional[str]
    uuid: str
    patient_program_id: Optional[int]
