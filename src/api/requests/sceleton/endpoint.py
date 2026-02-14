from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.api.models.base_model import BaseModel
from src.api.models.requests.create_patient_from_person_request import CreatePatientFromPersonRequest
from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.requests.create_provider_request import CreateProviderRequest
from src.api.models.requests.create_role_request import CreateRoleRequest
from src.api.models.requests.create_user_from_existing_person_request import CreateUserFromExistingPersonRequest
from src.api.models.requests.create_visit_request import CreateVisitRequest
from src.api.models.responses.create_patient_response import PatientFullResponse, PatientCreateResponse
from src.api.models.responses.create_person_response import CreatePersonResponse, PersonFullResponse
from src.api.models.responses.create_provider_response import CreateProviderResponse
from src.api.models.responses.create_role_response import CreateRoleResponse
from src.api.models.responses.create_user_response import CreateUserResponse
from src.api.models.responses.create_visit_response import CreateVisitResponse
from src.api.models.responses.get_location_response import LocationListResponse
from src.api.models.responses.get_privileges_response import GetPrivilegesResponse
from src.api.models.responses.get_roles_response import RoleListResponse
from src.api.models.responses.patient_identifier_type_response import PatientIdentifierTypeListResponse
from src.api.models.responses.get_visit_type_response import VisitTypeListResponse
from src.api.models.responses.get_visit_response import VisitFullResponse


@dataclass(frozen=True)
class EndpointConfig:
    url: str
    request_model: Optional[BaseModel]
    response_model: Optional[BaseModel]


class Endpoint(Enum):
    GET_ROLES = EndpointConfig(
        url="/role",
        request_model=None,
        response_model=RoleListResponse
    )

    CREATE_ROLE = EndpointConfig(
        url="/role",
        request_model=CreateRoleRequest,
        response_model=CreateRoleResponse
    )

    DELETE_ROLE = EndpointConfig(
        url="/role",
        request_model=None,
        response_model=None
    )

    GET_PRIVILEGES = EndpointConfig(
        url="/privilege",
        request_model=None,
        response_model=GetPrivilegesResponse
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
        response_model=CreatePersonResponse
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
        response_model=PatientFullResponse
    )

    CREATE_VISIT = EndpointConfig(
        url="/visit",
        request_model=CreateVisitRequest,
        response_model=CreateVisitResponse,
    )

    UPDATE_VISIT = EndpointConfig(
        url="/visit",
        request_model=CreateVisitRequest,
        response_model=CreateVisitResponse,
    )

    GET_VISIT = EndpointConfig(
        url="/visit",
        request_model=None,
        response_model=VisitFullResponse,
    )

    DELETE_VISIT = EndpointConfig(
        url="/visit",
        request_model=None,
        response_model=None,
    )

    GET_VISIT_TYPES = EndpointConfig(
        url="/visittype",
        request_model=None,
        response_model=VisitTypeListResponse,
    )

    CREATE_USER_FROM_PERSON = EndpointConfig(
        url="/user",
        request_model=CreateUserFromExistingPersonRequest,
        response_model=CreateUserResponse
    )

    DELETE_USER = EndpointConfig(
        url="/user",
        request_model=None,
        response_model=None
    )

    CREATE_PROVIDER = EndpointConfig(
        url="/provider",
        request_model=CreateProviderRequest,
        response_model=CreateProviderResponse
    )

    DELETE_PROVIDER = EndpointConfig(
        url="/provider",
        request_model=None,
        response_model=None
    )