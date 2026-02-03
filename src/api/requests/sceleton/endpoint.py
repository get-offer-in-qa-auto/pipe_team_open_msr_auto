from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.api.models.base_model import BaseModel
from src.api.models.requests.create_patient_from_person_request import CreatePatientFromPersonRequest
from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.responses.create_patient_response import PatientFullResponse, PatientCreateResponse
from src.api.models.responses.create_person_response import CreatPersonResponse, PersonFullResponse
from src.api.models.responses.get_location_response import LocationListResponse
from src.api.models.responses.get_roles_response import RoleListResponse
from src.api.models.responses.patient_identifier_type_response import PatientIdentifierTypeListResponse


@dataclass(frozen=True)
class EndpointConfig:
    url:str
    request_model:Optional[BaseModel]
    response_model:Optional[BaseModel]

class Endpoint(Enum):
    GET_ROLES = EndpointConfig(
        url="/role",
        request_model=None,
        response_model=RoleListResponse
    )

    GET_LOCATIONS = EndpointConfig(
        url="/location",
        request_model=None,
        response_model=LocationListResponse
    )

    GET_PATIENT_IDENTIFIER_TYPES = EndpointConfig(
        url="/patientidentifiertype",
        request_model=None,
        response_model=PatientIdentifierTypeListResponse
    )
    CREATE_PERSON = EndpointConfig(
        url="/person",
        request_model=CreatePersonRequest,
        response_model=CreatPersonResponse
    )

    GET_PERSON = EndpointConfig(
        url="/person",
        request_model=None,
        response_model=PersonFullResponse
    )

    DELETE_PERSON = EndpointConfig(
        url="/person",
        request_model=None,
        response_model=None
    )

    CREATE_PATIENT_FROM_PERSON = EndpointConfig(
        url="/patient",
        request_model=CreatePatientFromPersonRequest,
        response_model=PatientCreateResponse
    )

    DELETE_PATIENT = EndpointConfig(
        url="/patient",
        request_model=None,
        response_model=None
    )

    GET_PATIENT = EndpointConfig(
        url="/patient",
        request_model=None,
        response_model=PatientFullResponse  # добавим модель ниже
    )