from typing import List, Optional

from pydantic import BaseModel

from src.api.models.requests.create_patient_from_person_request import PatientIdentifierRequest


class PatientName(BaseModel):
    givenName: str
    familyName: Optional[str] = None


class PatientAddress(BaseModel):
    address1: str
    cityVillage: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None


class PatientPerson(BaseModel):
    gender: str
    birthdate: str
    names: List[PatientName]
    addresses: List[PatientAddress]


class CreatePatientRequest(BaseModel):
    identifiers: List[PatientIdentifierRequest]
    person: PatientPerson
