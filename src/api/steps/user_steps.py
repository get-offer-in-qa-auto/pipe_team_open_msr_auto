from __future__ import annotations

from typing import Optional, List, Any, Callable

from src.api.constants.error_messages import ErrorMessages
from src.api.generators.mod30 import generate_mod30_identifier
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.comparison.model_assertions import ModelAssertions
from src.api.models.requests.BaseCreateUserRequest import BaseCreateUserRequest
from src.api.models.requests.create_patient_from_person_request import (
    CreatePatientFromPersonRequest,
    PatientIdentifierRequest,
)
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
        return self._vcr(Endpoint.GET_PERSON, ResponseSpecs.request_returns_ok()).get(
            id=person_uuid, params={"v": "full"}
        )

    def get_patient_full(self, patient_uuid: str) -> PatientFullResponse:
        return self._vcr(Endpoint.GET_PATIENT, ResponseSpecs.request_returns_ok()).get(
            id=patient_uuid, params={"v": "full"}
        )

    def verify_patient_with_uuid_does_not_exist(self, patient_uuid: str):
        self._cr(Endpoint.GET_PATIENT, ResponseSpecs.entity_not_found(ErrorMessages.OBJECT_WITH_UUID_DOES_NOT_EXIST)).get(
            id=patient_uuid,
        )

    def create_person(self, create_person_request: CreatePersonRequest) -> CreatePersonResponse:
        person = self._vcr(Endpoint.CREATE_PERSON, ResponseSpecs.entity_was_created()).post(create_person_request)

        assert person.uuid
        assert person.voided is False
        assert person.preferredName.uuid
        #TODO: тут по полям матчить

        self.created_objects.append(person)
        return person

    def delete_person(self, person_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None
        self._cr(Endpoint.DELETE_PERSON, ResponseSpecs.entity_was_deleted()).delete_with_params(
            id=person_uuid, params=params
        )

    def create_invalid_person(self, create_person_request: CreatePersonInvalidRequest, error_value: str, error_key: str ="error",):
        self._cr(
            Endpoint.CREATE_PERSON,
            ResponseSpecs.request_returns_bad_request(error_key, error_value),
        ).post(create_person_request)

    def create_patient_from_person(
        self,
        person: str,
        identifiers: Optional[List[PatientIdentifierRequest]] = None,
        user_request: Optional[BaseCreateUserRequest] = None,
    ) -> PatientCreateResponse:
        request_spec = (
            RequestSpecs.auth_as_user(user_request.username, user_request.password)
            if user_request
            else RequestSpecs.admin_auth_spec()
        )

        identifiers = identifiers or [self.build_identifier_request()]
        req = CreatePatientFromPersonRequest(person=person, identifiers=identifiers)

        patient_created = ValidatedCrudRequester(
            request_spec=request_spec,
            endpoint=Endpoint.CREATE_PATIENT_FROM_PERSON,
            response_spec=ResponseSpecs.entity_was_created(),
        ).post(req)

        assert patient_created.uuid, f"patient_created.uuid is falsy: {patient_created}"
        assert patient_created.uuid == person, f"Verify returned uuid is: {person}, but got {patient_created.uuid}"
        assert str(patient_created.uuid).lower() != "null", f"uuid returned as 'null': {patient_created}"



        self.created_objects.append(patient_created)
        return patient_created

    def verify_patient_created(self,
                               created_patient_response: PatientCreateResponse,
                               identifiers: List[PatientIdentifierRequest]):
        req = CreatePatientFromPersonRequest(person=created_patient_response.uuid, identifiers=identifiers)
        patient_full = self.get_patient_full(created_patient_response.uuid)
        ModelAssertions(req, patient_full).match()

    def verify_person_created(self, person_uuid, expected_request=None):
        full = self.get_person_full(person_uuid)

        assert full.uuid == person_uuid
        assert full.voided is False
        assert full.preferredName
        assert full.preferredName.uuid

        if expected_request:
            ModelAssertions(expected_request, full).match()
        return full

    def create_patient_from_person_invalid_data(
        self,
        person: str,
        error_message: str,
        identifiers: Optional[List[PatientIdentifierRequest]] = None,
        user_request: Optional[BaseCreateUserRequest] = None,
    ):
        request_spec = (
            RequestSpecs.auth_as_user(user_request.username, user_request.password)
            if user_request
            else RequestSpecs.admin_auth_spec()
        )

        req = CreatePatientFromPersonRequest(person=person, identifiers=identifiers)
        CrudRequester(
            request_spec=request_spec,
            endpoint=Endpoint.CREATE_PATIENT_FROM_PERSON,
            response_spec=ResponseSpecs.request_returns_bad_request_with_message(error_message),
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

    def create_patient_with_person(
        self,
        create_person_request: CreatePersonRequest,
        identifiers: Optional[List[PatientIdentifierRequest]] = None,
    ):
        created_person = self.create_person(create_person_request)
        created_patient = self.create_patient_from_person(created_person.uuid, identifiers)

        assert created_patient.uuid
        assert created_patient.display

        return created_person, created_patient

    def create_patient_from_existing_person(self) -> PatientCreateResponse:
        _, patient = self.create_patient_with_person(RandomModelGenerator.generate(CreatePersonRequest))
        return patient

    def delete_patient(self, patient_uuid: str):
        for visit_uuid in self._get_visit_uuids_by_patient(patient_uuid):
            self._purge_visit(visit_uuid)

        self._cr(Endpoint.DELETE_PATIENT, ResponseSpecs.entity_was_deleted()).delete_with_params(
            id=patient_uuid, params={"purge": "true"}
        )

    def create_user_from_existing_person(self, create_user_request: CreateUserFromExistingPersonRequest) -> CreateUserResponse:
        user = self._vcr(Endpoint.CREATE_USER_FROM_PERSON, ResponseSpecs.entity_was_created()).post(create_user_request)
        ModelAssertions(create_user_request, user).match()

        self.created_objects.append(user)
        return user

    def delete_user(self, user_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None
        self._cr(Endpoint.DELETE_USER, ResponseSpecs.entity_was_deleted()).delete_with_params(id=user_uuid, params=params)

    def create_provider(self, create_provider_request: CreateProviderRequest):
        provider = self._vcr(Endpoint.CREATE_PROVIDER, ResponseSpecs.entity_was_created()).post(create_provider_request)
        self.created_objects.append(provider)
        return provider

    def delete_provider(self, provider_uuid: str, purge: bool = True):
        params = {"purge": "true"} if purge else None
        self._cr(Endpoint.DELETE_PROVIDER, ResponseSpecs.entity_was_deleted()).delete_with_params(
            id=provider_uuid, params=params
        )

    def get_locations(self):
        return self._vcr(Endpoint.GET_LOCATIONS, ResponseSpecs.request_returns_ok()).get()

    def get_visit_types(self):
        return self._vcr(Endpoint.GET_VISIT_TYPES, ResponseSpecs.request_returns_ok()).get()

    def get_patient_identifier_types(self):
        return self._vcr(Endpoint.GET_PATIENT_IDENTIFIER_TYPES, ResponseSpecs.request_returns_ok()).get()

    def build_identifier_request(self) -> PatientIdentifierRequest:
        identifier_types = self.get_patient_identifier_types()
        locations = self.get_locations()

        identifier_type_uuid = identifier_types.results[0].uuid
        location_uuid = locations.results[0].uuid

        return PatientIdentifierRequest(
            identifier=generate_mod30_identifier(total_len=10),
            identifierType=identifier_type_uuid,
            location=location_uuid,
            preferred=True,
        )

    def _get_visit_uuids_by_patient(self, patient_uuid: str) -> List[str]:
        resp = self._cr(Endpoint.GET_VISIT, ResponseSpecs.request_returns_ok()).get(params={"patient": patient_uuid})

        try:
            body: dict[str, Any] = resp.json()
            results = body.get("results", [])
            return [v["uuid"] for v in results if isinstance(v, dict) and v.get("uuid")]
        except Exception:
            return []

    def _purge_visit(self, visit_uuid: str):
        self._cr(Endpoint.DELETE_VISIT, ResponseSpecs.entity_was_deleted()).delete_with_params(
            id=visit_uuid, params={"purge": "true"}
        )