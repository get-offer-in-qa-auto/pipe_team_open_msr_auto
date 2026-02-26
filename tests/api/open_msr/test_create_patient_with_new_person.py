import pytest

from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.requests.sceleton.requesters.crud_requester import CrudRequester
from src.api.specs.request_spec import RequestSpecs
from src.api.classes.api_manager import ApiManager
from src.api.constants.error_messages import ErrorMessages
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.generators.random_data import RandomData
from src.api.models.requests.create_patient_request import CreatePatientRequest
from src.api.specs.response_spec import ResponseSpecs
from src.api.requests.sceleton.requesters.crud_requester import CrudRequester
from src.api.specs.request_spec import RequestSpecs
from src.api.requests.sceleton.endpoint import Endpoint

@pytest.mark.api
class TestCreatePatientWithNewPerson:
    # --------------------------------------------------
    # ADMIN happy path
    # --------------------------------------------------
    @pytest.mark.check_all_patients_change(delta=1, should_exist=True)
    def test_create_patient_with_new_person_admin(
        self,
        api_manager: ApiManager
    ):
        request = api_manager.user_steps.build_create_patient_request()
        patient = api_manager.user_steps.create_patient(request)

        api_manager.database_steps.verify_patient_created_with_new_person(
            patient_uuid=patient.uuid,
            identifiers=request.identifiers
        )
    # --------------------------------------------------
    # Allowed roles
    # --------------------------------------------------
    @pytest.mark.check_all_patients_change(delta=1, should_exist=True)
    @pytest.mark.usefixtures("create_user_with_roles")
    @pytest.mark.parametrize("role", [
        "Registration Clerk",
    ])
    def test_create_patient_with_new_person_allowed_roles(
        self,
        api_manager,
        create_user_with_roles,
        role
    ):
        user_request, _ = create_user_with_roles()

        request = api_manager.user_steps.build_create_patient_request()

        patient = api_manager.user_steps.create_patient(
            patient_request=request,
            user_request=user_request
        )

        api_manager.database_steps.verify_patient_created_with_new_person(
            patient_uuid=patient.uuid,
            identifiers=request.identifiers
        )
    # --------------------------------------------------
    # Forbidden roles
    # --------------------------------------------------
    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    @pytest.mark.usefixtures("create_user_with_privileges")
    def test_create_patient_with_new_person_without_required_privileges(
            self,
            api_manager,
            create_user_with_privileges
    ):
        exclude_privilege_names = ['Add Patients', 'Edit Patients']

        user_request, _ = create_user_with_privileges(
            exclude_privilege_names=exclude_privilege_names
        )

        request = api_manager.user_steps.build_create_patient_request()

        error_message = ErrorMessages.privileges_required(exclude_privilege_names)

        api_manager.user_steps.create_patient_invalid_request(
            patient_request=request,
            user_request=user_request,
            response_spec=ResponseSpecs.request_returns_forbidden_with_message(error_message)
        )

    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    def test_create_patient_with_new_person_disabled_user(
            self,
            api_manager,
            create_user_with_roles
    ):
        user_request, user_data = create_user_with_roles()

        api_manager.user_steps.delete_user(user_data.uuid, purge=False)

        # ✅ создаём request один раз
        request = api_manager.user_steps.build_create_patient_request()

        original_identifier = request.identifiers[0].identifier

        api_manager.user_steps.create_patient_with_new_person_invalid_request(
            patient_request=request,
            user_request=user_request,
            response_spec=ResponseSpecs.request_returns_bad_request_with_message(
                "Privileges required: Get Identifier Types"
            )
        )

        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

    # invalid person root field
    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    def test_create_patient_missing_person(self, api_manager):
        request = api_manager.user_steps.build_create_patient_request()

        original_identifier = request.identifiers[0].identifier

        del request.person

        api_manager.user_steps.create_patient_with_new_person_invalid_request(
            patient_request=request,
            response_spec=ResponseSpecs.request_returns_bad_request_with_message("person")
        )

        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )