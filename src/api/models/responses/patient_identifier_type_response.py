from typing import List
from src.api.models.base_model import BaseModel


class PatientIdentifierTypeLink(BaseModel):
    rel: str
    uri: str
    resourceAlias: str


class PatientIdentifierTypeResult(BaseModel):
    uuid: str
    display: str
    links: List[PatientIdentifierTypeLink]


class PatientIdentifierTypeListResponse(BaseModel):
    results: List[PatientIdentifierTypeResult]
