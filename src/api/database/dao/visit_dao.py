from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VisitDao:
    visit_id: int
    patient_id: int
    visit_type_id: int
    date_started: datetime
    date_stopped: Optional[datetime]
    indication_concept_id: Optional[int]
    location_id: Optional[int]
    creator: int
    date_created: datetime
    changed_by: Optional[int]
    date_changed: Optional[datetime]
    voided: int
    voided_by: Optional[int]
    date_voided: Optional[datetime]
    void_reason: Optional[str]
    uuid: str
