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

    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    def test_create_patient_rollback_on_invalid_identifier(self, api_manager):
        request = api_manager.user_steps.build_create_patient_request()

        original_identifier = request.identifiers[0].identifier
        original_given_name = request.person.names[0].givenName
        original_family_name = request.person.names[0].familyName
        original_birthdate = request.person.birthdate

        # ломаем identifier
        request.identifiers[0].identifier = ""

        api_manager.user_steps.create_patient_with_new_person_invalid_request(
            patient_request=request,
            response_spec=ResponseSpecs.request_returns_bad_request_with_message(
                ErrorMessages.INVALID_SUBMISSION
            )
        )

        # patient не создан
        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

        # person не создан (rollback check)
        api_manager.database_steps.verify_person_not_created_by_identity(
            given_name=original_given_name,
            family_name=original_family_name,
            birthdate=original_birthdate
        )

    @pytest.mark.api
    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    @pytest.mark.parametrize(
        "field, value, error_message",
        [
            # identifierType
            ("identifierType", "", ErrorMessages.EMPTY_IDENTIFIER_TYPE),
            ("identifierType", None, ErrorMessages.EMPTY_IDENTIFIER_TYPE),
            ("identifierType", RandomData.get_int(1, 1000), ErrorMessages.INT_IDENTIFIER_TYPE),
            ("identifierType", RandomData.get_word(), ErrorMessages.EMPTY_IDENTIFIER_TYPE),
            ("identifierType", str(RandomData.get_uuid()), ErrorMessages.EMPTY_IDENTIFIER_TYPE),

            # location
            ("location", "", ErrorMessages.EMPTY_LOCATION),
            ("location", None, ErrorMessages.EMPTY_LOCATION),
            ("location", RandomData.get_int(1, 1000), ErrorMessages.INT_LOCATION),
            ("location", RandomData.get_word(), ErrorMessages.EMPTY_LOCATION),
            ("location", str(RandomData.get_uuid()), ErrorMessages.EMPTY_LOCATION),

            # identifier
            ("identifier", "", ErrorMessages.INVALID_SUBMISSION),
            ("identifier", None, ErrorMessages.INVALID_SUBMISSION),
            ("identifier", RandomData.get_int(1, 1000), ErrorMessages.INT_IDENTIFIER),
            ("identifier", RandomData.get_word(), ErrorMessages.INVALID_SUBMISSION),
            ("identifier", "a", ErrorMessages.INVALID_SUBMISSION),
            ("identifier", "MRN#123", ErrorMessages.INVALID_SUBMISSION),
            ("identifier", RandomData.get_string(256), ErrorMessages.INVALID_SUBMISSION),
        ],
    )
    def test_create_patient_with_new_person_invalid_identifier(
            self,
            api_manager,
            field,
            value,
            error_message
    ):
        request = api_manager.user_steps.build_create_patient_request()

        identifier = request.identifiers[0]

        original_identifier = identifier.identifier
        original_given_name = request.person.names[0].givenName
        original_family_name = request.person.names[0].familyName
        original_birthdate = request.person.birthdate

        setattr(identifier, field, value)

        api_manager.user_steps.create_patient_with_new_person_invalid_request(
            patient_request=request,
            response_spec=ResponseSpecs.request_returns_bad_request_with_message(
                error_message
            )
        )

        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

        api_manager.database_steps.verify_person_not_created_by_identity(
            given_name=original_given_name,
            family_name=original_family_name,
            birthdate=original_birthdate
        )