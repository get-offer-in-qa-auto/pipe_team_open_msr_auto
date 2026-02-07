import pytest

from src.api.constants.error_messages import ErrorMessages
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest


@pytest.mark.api
class TestCreatePatientFromExistingPerson:
    def test_create_patient_from_existing_person_admin_user(self, api_manager):
        api_manager.user_steps.create_patient_with_person(RandomModelGenerator.generate(CreatePersonRequest))

    @pytest.mark.usefixtures('api_manager', 'created_person', 'create_user_with_roles')
    @pytest.mark.parametrize('role',[
        "Privilege Level: Full",
        "Privilege Level: High",
        "Organizational: Doctor",
    ])
    def test_create_patient_from_existing_person_with_role(self, api_manager, create_user_with_roles, created_person, role):
        user_request = create_user_with_roles(roles=[role])

        api_manager.user_steps.create_patient_from_person(person=created_person.uuid, user_request=user_request)

    @pytest.mark.usefixtures('api_manager', 'created_person', 'create_user_with_roles')
    @pytest.mark.parametrize('identifier_type, error_message', [
        ("", ErrorMessages.EMPTY_IDENTIFIER_TYPE),
        (None, ErrorMessages.EMPTY_STRING_IDENTIFIER_TYPE),
        (123, ErrorMessages.INT_IDENTIFIER_TYPE),
    ])
    def test_create_patient_from_existing_person_invalid_identifier_type(self, api_manager, create_user_with_roles,
                                                                         created_person, identifier_type, error_message):
        user_request = create_user_with_roles()

        identifier = api_manager.user_steps.get_identifier_request()
        identifier.identifierType = identifier_type

        api_manager.user_steps.create_patient_from_person_invalid_data(person=created_person.uuid,
                                                                       error_message=error_message,
                                                                       identifiers=[identifier],
                                                                       user_request=user_request)
