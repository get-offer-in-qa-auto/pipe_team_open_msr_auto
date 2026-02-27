from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PersonNameDao:
    person_name_id: int
    preferred: bool
    person_id: int
    prefix: Optional[str]
    given_name: str
    middle_name: Optional[str]
    family_name_prefix: Optional[str]
    family_name: str
    family_name2: Optional[str]
    family_name_suffix: Optional[str]
    degree: Optional[str]
    creator: int
    date_created: datetime
    voided: bool
    voided_by: Optional[int]
    date_voided: Optional[datetime]
    void_reason: Optional[str]
    changed_by: Optional[int]
    date_changed: Optional[datetime]
    uuid: str
