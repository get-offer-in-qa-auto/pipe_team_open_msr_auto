from pydantic import BaseModel
from typing import List, Optional


class PatientName(BaseModel):
    givenName: str
    familyName: Optional[str] = None


class PatientPerson(BaseModel):
    gender: str
    birthdate: str
    names: List[PatientName]

class UuidRef(BaseModel):
    uuid: str

class PatientIdentifier(BaseModel):
    identifier: str
    identifierType: UuidRef
    location: UuidRef
    preferred: bool = True


class CreatePatientRequest(BaseModel):
    identifiers: List[PatientIdentifier]
    person: PatientPerson
