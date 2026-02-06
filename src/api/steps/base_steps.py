from typing import Any
from typing import Optional, List

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_patient_from_person_request import PatientIdentifierRequest
from src.api.models.responses.get_roles_response import RoleListResponse
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.requests.sceleton.requesters.validated_crud_requester import ValidatedCrudRequester
from src.api.specs.request_spec import RequestSpecs
from src.api.specs.response_spec import ResponseSpecs


class BaseSteps:
    def __init__(self, created_objects: List[Any]):
        self.created_objects = created_objects

    def get_roles(self) -> RoleListResponse:
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_ROLES,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get()

    def get_locations(self):
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_LOCATIONS,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get()

    def get_patient_identifier_types(self):
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_PATIENT_IDENTIFIER_TYPES,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get()

    def get_identifier_request(
            self,
            identifier_request: Optional[PatientIdentifierRequest] = RandomModelGenerator.generate(PatientIdentifierRequest)
    ):
        types = self.get_patient_identifier_types()
        identifier_type_uuid = types.results[0].uuid

        locations = self.get_locations()
        location_uuid = locations.results[0].uuid

        identifier_request.identifierType = identifier_type_uuid
        identifier_request.location = location_uuid
        identifier_request.preferred = True

        return identifier_request

