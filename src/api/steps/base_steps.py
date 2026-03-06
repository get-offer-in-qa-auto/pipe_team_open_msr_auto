import allure
import random
from typing import Any
from typing import Optional, List

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_patient_from_person_request import PatientIdentifierRequest
from src.api.models.requests.create_role_request import CreateRoleRequest, CreateRolePrivilegeModel
from src.api.models.responses.create_role_response import CreateRoleResponse
from src.api.models.responses.get_privileges_response import GetPrivilegesResponse, GetPrivilegesModel
from src.api.models.responses.get_roles_response import RoleListResponse
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.requests.sceleton.requesters.crud_requester import CrudRequester
from src.api.requests.sceleton.requesters.validated_crud_requester import ValidatedCrudRequester
from src.api.specs.request_spec import RequestSpecs
from src.api.specs.response_spec import ResponseSpecs


class BaseSteps:
    @allure.step("__init__")
    def __init__(self, created_objects: List[Any]):
        self.created_objects = created_objects

    @allure.step("_request_spec")
    def _request_spec(self, request_spec=None):
        return request_spec or RequestSpecs.admin_auth_spec()

    @allure.step("_vcr")
    def _vcr(self, endpoint: Endpoint, response_spec, request_spec=None) -> ValidatedCrudRequester:
        return ValidatedCrudRequester(
            request_spec=self._request_spec(request_spec),
            endpoint=endpoint,
            response_spec=response_spec,
        )

    @allure.step("_cr")
    def _cr(self, endpoint: Endpoint, response_spec, request_spec=None) -> CrudRequester:
        return CrudRequester(
            request_spec=self._request_spec(request_spec),
            endpoint=endpoint,
            response_spec=response_spec,
        )

    @allure.step("get_roles")
    def get_roles(self) -> RoleListResponse:
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_ROLES,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get()

    @allure.step("create_role")
    def create_role(self, create_role_request: CreateRoleRequest) -> CreateRoleResponse:
        create_role_response: CreateRoleResponse = ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.CREATE_ROLE,
            response_spec=ResponseSpecs.entity_was_created()
        ).post(create_role_request)

        self.created_objects.append(create_role_response)
        return create_role_response

    @allure.step("create_role_with_excluded_privileges")
    def create_role_with_excluded_privileges(self, excluded_privileges: List[str]) -> CreateRoleResponse:
        """
        :param excluded_privileges: excluded privileges display names list
        :return: CreateRoleResponse
        """
        privileges = self.get_all_privileges()
        privileges_to_include = [CreateRolePrivilegeModel(name=privilege.name, description=privilege.description)
                                 for privilege in privileges.results
                                 if privilege.display not in excluded_privileges]
        role_request: CreateRoleRequest = RandomModelGenerator.generate(CreateRoleRequest)
        role_request.privileges = privileges_to_include
        return self.create_role(role_request)

    @allure.step("delete_role")
    def delete_role(self, role_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None

        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.DELETE_ROLE,
            response_spec=ResponseSpecs.entity_was_deleted()
        ).delete_with_params(id=role_uuid, params=params)

    @allure.step("get_locations")
    def get_locations(self):
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_LOCATIONS,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get()

    @allure.step("get_patient_identifier_types")
    def get_patient_identifier_types(self):
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_PATIENT_IDENTIFIER_TYPES,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get()

    @allure.step("get_identifier_request")
    def get_identifier_request(
            self,
            identifier_request: Optional[PatientIdentifierRequest] = RandomModelGenerator.generate(PatientIdentifierRequest)
    ) -> PatientIdentifierRequest:
        types = self.get_patient_identifier_types()
        identifier_type_uuid = types.results[0].uuid

        locations = self.get_locations()
        location_uuid = random.choice(locations.results).uuid

        identifier_request.identifierType = identifier_type_uuid
        identifier_request.location = location_uuid
        identifier_request.preferred = True

        return identifier_request

    @allure.step("get_privileges")
    def get_privileges(self, start_index: Optional[int] = 1) -> GetPrivilegesResponse:
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_PRIVILEGES,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get(params={"v": "full",
                      "limit": "100",
                      "startIndex": start_index})

    @allure.step("get_all_privileges")
    def get_all_privileges(self) -> GetPrivilegesResponse:
        all_privileges: List[GetPrivilegesModel] = []
        limit = 100
        start_index = 0

        while True:
            privileges = self.get_privileges(start_index=start_index)
            all_privileges.extend(privileges.results)

            # Если пришло меньше, чем лимит — мы достигли конца списка
            if len(privileges.results) < limit:
                break

            start_index += limit

        return GetPrivilegesResponse(results=all_privileges)



