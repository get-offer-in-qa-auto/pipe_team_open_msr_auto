from typing import List, Annotated

from src.api.generators.generating_rule import GeneratingRule
from src.api.models.base_model import BaseModel

class UuidRef(BaseModel):
    uuid: str


class PatientIdentifierRequest(BaseModel):
    identifier: str
    identifierType: UuidRef
    location: UuidRef
    preferred: bool = True

class CreatePatientFromPersonRequest(BaseModel):
    person: str  # uuid существующей Person
    identifiers: List[PatientIdentifierRequest]
