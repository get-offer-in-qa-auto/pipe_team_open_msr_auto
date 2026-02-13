from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PersonDao:
    person_id: int
    gender: str
    birthdate: Optional[datetime]
    birthdate_estimated: bool
    dead: bool
    death_date: Optional[datetime]
    cause_of_death: Optional[str]
    creator: int
    date_created: datetime
    changed_by: Optional[int]
    date_changed: Optional[datetime]
    voided: bool
    voided_by: Optional[int]
    date_voided: Optional[datetime]
    void_reason: Optional[str]
    uuid: str
    deathdate_estimated: bool
    birthtime: Optional[datetime]
    cause_of_death_non_coded: Optional[str]


