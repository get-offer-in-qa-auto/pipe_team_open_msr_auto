from dataclasses import dataclass
from datetime import datetime


@dataclass
class PersonDao:
    person_id: int
    gender: str
    birthdate: datetime | None
    birthdate_estimated: bool
    dead: bool
    death_date: datetime | None
    cause_of_death: str | None
    creator: int
    date_created: datetime
    changed_by: int | None
    date_changed: datetime | None
    voided: bool
    voided_by: int | None
    date_voided: datetime | None
    void_reason: str | None
    uuid: str
    deathdate_estimated: bool
    birthtime: datetime | None
    cause_of_death_non_coded: str | None


