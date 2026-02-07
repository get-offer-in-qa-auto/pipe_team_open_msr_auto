from typing import Optional, List, Callable

from src.api.models.comparison.model_assertions import ModelAssertions
from src.api.models.requests.BaseCreateUserRequest import BaseCreateUserRequest
from src.api.models.requests.create_patient_from_person_request import CreatePatientFromPersonRequest, \
    PatientIdentifierRequest
from src.api.models.requests.create_person_request import CreatePersonRequest, CreatePersonInvalidRequest
from src.api.models.requests.create_provider_request import CreateProviderRequest
from src.api.models.requests.create_user_from_existing_person_request import CreateUserFromExistingPersonRequest
from src.api.models.responses.create_patient_response import PatientCreateResponse, PatientFullResponse
from src.api.models.responses.create_person_response import CreatePersonResponse, PersonFullResponse
from src.api.models.responses.create_user_response import CreateUserResponse
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.requests.sceleton.requesters.crud_requester import CrudRequester
from src.api.requests.sceleton.requesters.validated_crud_requester import ValidatedCrudRequester
from src.api.specs.request_spec import RequestSpecs
from src.api.specs.response_spec import ResponseSpecs
from src.api.steps.base_steps import BaseSteps


class UserSteps(BaseSteps):
    def get_person_full(self, person_uuid: str) -> PersonFullResponse:
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_PERSON,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get(id=person_uuid, params={"v": "full"})

    def get_patient_full(self, patient_uuid: str) -> PatientFullResponse:
        return ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.GET_PATIENT,
            response_spec=ResponseSpecs.request_returns_ok()
        ).get(id=patient_uuid, params={"v": "full"})

    def create_person(self, create_person_request: CreatePersonRequest) -> CreatePersonResponse:
        person = ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.CREATE_PERSON,
            response_spec=ResponseSpecs.entity_was_created()
        ).post(create_person_request)

        full = self.get_person_full(person.uuid)
        ModelAssertions(create_person_request, full).match()
        self.created_objects.append(person)
        return person

    def delete_person(self, person_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None

        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.DELETE_PERSON,
            response_spec=ResponseSpecs.entity_was_deleted()
        ).delete_with_params(id=person_uuid, params=params)

    def create_patient_from_person(self,
                                   person: str,
                                   identifiers: Optional[List[PatientIdentifierRequest]] = None,
                                   user_request: Optional[BaseCreateUserRequest] = None) -> PatientCreateResponse:
        request_spec = RequestSpecs.auth_as_user(user_request.username, user_request.password) if user_request else RequestSpecs.admin_auth_spec()
        identifiers = identifiers or [self.get_identifier_request()]
        req = CreatePatientFromPersonRequest(person=person, identifiers=identifiers)

        patient_created = ValidatedCrudRequester(
            request_spec=request_spec,
            endpoint=Endpoint.CREATE_PATIENT_FROM_PERSON,
            response_spec=ResponseSpecs.entity_was_created()
        ).post(req)

        assert patient_created.uuid, f"patient_created.uuid is falsy: {patient_created}"
        assert str(patient_created.uuid).lower() != "null", f"uuid returned as 'null': {patient_created}"

        patient_full = self.get_patient_full(patient_created.uuid)
        ModelAssertions(req, patient_full).match()

        self.created_objects.append(patient_created)
        return patient_created

    def delete_patient(self, patient_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None
        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.DELETE_PATIENT,
            response_spec=ResponseSpecs.entity_was_deleted()
        ).delete_with_params(id=patient_uuid, params=params)

    def create_patient_from_person_invalid_data(
            self,
            person: str,
            error_message: str,
            identifiers: Optional[List[PatientIdentifierRequest]] = None,
            user_request: Optional[BaseCreateUserRequest] = None):
        request_spec = RequestSpecs.auth_as_user(user_request.username, user_request.password) if user_request else RequestSpecs.admin_auth_spec()
        req = CreatePatientFromPersonRequest(person=person, identifiers=identifiers)

        CrudRequester(
            request_spec=request_spec,
            endpoint=Endpoint.CREATE_PATIENT_FROM_PERSON,
            response_spec=ResponseSpecs.request_returns_bad_request_with_message(error_message)
        ).post(req)

    def create_patient_from_person_invalid_request(
            self,
            person: str,
            user_request: BaseCreateUserRequest,
            response_spec: Callable,
            identifiers: Optional[List[PatientIdentifierRequest]] = None,
        ):
        req = CreatePatientFromPersonRequest(person=person, identifiers=identifiers)

        CrudRequester(
            request_spec=RequestSpecs.auth_as_user(user_request.username, user_request.password),
            endpoint=Endpoint.CREATE_PATIENT_FROM_PERSON,
            response_spec=response_spec
        ).post(req)

    # def create_patient_from_person_forbidden_request(
    #         self,
    #         person: str,
    #         error_message: str,
    #         user_request: BaseCreateUserRequest,
    #         identifiers: Optional[List[PatientIdentifierRequest]] = None,
    #     ):
    #     req = CreatePatientFromPersonRequest(person=person, identifiers=identifiers)
    #
    #     CrudRequester(
    #         request_spec=RequestSpecs.auth_as_user(user_request.username, user_request.password),
    #         endpoint=Endpoint.CREATE_PATIENT_FROM_PERSON,
    #         response_spec=ResponseSpecs.request_returns_forbidden_with_message(error_message)
    #     ).post(req)

    def delete_patient(self, patient_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None
        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.DELETE_PATIENT,
            response_spec=ResponseSpecs.entity_was_deleted()
        ).delete_with_params(id=patient_uuid, params=params)

    def create_invalid_person(self, create_person_request: CreatePersonInvalidRequest, error_key, error_value):
        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.CREATE_PERSON,
            response_spec=ResponseSpecs.request_returns_bad_request(error_key, error_value),
        ).post(create_person_request)

    def create_patient_with_person(
        self, create_person_request: CreatePersonRequest, identifiers: Optional[List[PatientIdentifierRequest]] = None,
    ):
        created_person = self.create_person(create_person_request)

        identifiers = identifiers or [self.get_identifier_request()]

        created_patient = self.create_patient_from_person(created_person.uuid, identifiers)

        assert created_patient.uuid
        assert created_patient.display

        return created_person, created_patient

    def create_user_from_existing_person(self, create_user_request: CreateUserFromExistingPersonRequest) -> CreateUserResponse:
        create_user_response: CreateUserResponse = ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.CREATE_USER_FROM_PERSON,
            response_spec=ResponseSpecs.entity_was_created()
        ).post(create_user_request)

        ModelAssertions(create_user_request, create_user_response).match()
        self.created_objects.append(create_user_response)
        return create_user_response

    def delete_user(self, user_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None

        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.DELETE_USER,
            response_spec=ResponseSpecs.entity_was_deleted()
        ).delete_with_params(id=user_uuid, params=params)

    def create_provider(self, create_provider_request: CreateProviderRequest):
        response = ValidatedCrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.CREATE_PROVIDER,
            response_spec=ResponseSpecs.entity_was_created()
        ).post(create_provider_request)

        self.created_objects.append(response)

        return response

    def delete_provider(self, provider_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None

        CrudRequester(
            request_spec=RequestSpecs.admin_auth_spec(),
            endpoint=Endpoint.DELETE_PROVIDER,
            response_spec=ResponseSpecs.entity_was_deleted()
        ).delete_with_params(id=provider_uuid, params=params)