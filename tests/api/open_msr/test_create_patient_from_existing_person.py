import pytest

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest


@pytest.mark.api
class TestCreatePatientFromExistingPerson:
    def test_create_patient_from_existing_person_admin_user(self, api_manager):
        api_manager.user_steps.create_patient_with_person(RandomModelGenerator.generate(CreatePersonRequest))

    @pytest.mark.debug
    @pytest.mark.skip(reason="TEST EXAMPLE with 'full_privilege_user' fixture: will be deleted")
    @pytest.mark.usefixtures('api_manager', 'full_privilege_user')
    def test_create_patient_from_existing_person_with_full_privilege_user(self, api_manager, full_privilege_user):
        user_request, _, _ = full_privilege_user

        create_person_request: CreatePersonRequest = RandomModelGenerator.generate(CreatePersonRequest)
        created_person = api_manager.user_steps.create_person(create_person_request)
        api_manager.user_steps.create_patient_from_person(person=created_person.uuid, user_request=user_request)

    @pytest.mark.usefixtures('api_manager', 'create_user_with_roles')
    @pytest.mark.parametrize('role',[
        "Privilege Level: Full",
        "Privilege Level: High",
        "Organizational: Doctor",
    ])
    def test_create_patient_from_existing_person_with_role(self, api_manager, create_user_with_roles, role):
        user_request = create_user_with_roles(roles=[role])

        created_person = api_manager.user_steps.create_person(RandomModelGenerator.generate(CreatePersonRequest))
        api_manager.user_steps.create_patient_from_person(person=created_person.uuid, user_request=user_request)
