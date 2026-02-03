from typing import List, Annotated

from src.api.generators.generating_rule import GeneratingRule
from src.api.models.base_model import BaseModel


class PatientIdentifierRequest(BaseModel):
    # В OpenMRS identifier — произвольная строка, но пусть будет "безопасная" генерация
    identifier: Annotated[str, GeneratingRule(regex=r"^[A-Za-z0-9]{5,12}$")]
    identifierType: str  # uuid
    location: str        # uuid
    preferred: bool = False


class CreatePatientFromPersonRequest(BaseModel):
    person: str  # uuid существующей Person
    identifiers: List[PatientIdentifierRequest]
