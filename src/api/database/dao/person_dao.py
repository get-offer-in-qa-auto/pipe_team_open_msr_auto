from dataclasses import dataclass
from datetime import datetime
from typing import Optional


from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PersonAddressDao:
    person_address_id: int
    person_id: int

    preferred: bool

    # Address fields (OpenMRS)
    address1: Optional[str]
    address2: Optional[str]
    address3: Optional[str]
    address4: Optional[str]
    address5: Optional[str]
    address6: Optional[str]
    address7: Optional[str]
    address8: Optional[str]
    address9: Optional[str]
    address10: Optional[str]
    address11: Optional[str]
    address12: Optional[str]
    address13: Optional[str]
    address14: Optional[str]
    address15: Optional[str]

    city_village: Optional[str]
    county_district: Optional[str]
    state_province: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]

    latitude: Optional[str]
    longitude: Optional[str]

    start_date: Optional[datetime]
    end_date: Optional[datetime]

    # Audit fields
    creator: Optional[int]
    date_created: datetime
    changed_by: Optional[int]
    date_changed: Optional[datetime]

    # Voiding fields
    voided: bool
    voided_by: Optional[int]
    date_voided: Optional[datetime]
    void_reason: Optional[str]

    uuid: str

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


