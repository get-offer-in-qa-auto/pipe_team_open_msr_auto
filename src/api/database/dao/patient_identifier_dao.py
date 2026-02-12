import datetime
from dataclasses import dataclass


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
    date_changed: datetime.datetime | None
    changed_by: int
    voided: str | None
    voided_by: int | None
    date_voided: datetime.datetime | None
    void_reason: str | None
    uuid: str
    patient_program_id: int | None

