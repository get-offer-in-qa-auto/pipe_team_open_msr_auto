import pytest

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.requests.update_person_request import UpdatePersonRequest


@pytest.mark.api
class TestUpdatePerson:
    @pytest.mark.usefixtures('api_manager', 'created_person')
    def test_update_person_gender(self, api_manager, created_person):
        new_user_data = RandomModelGenerator.generate(CreatePersonRequest)
        update_req = UpdatePersonRequest(gender=new_user_data.gender)

        updated_person_response = api_manager.user_steps.update_person(
            person_uuid=created_person.uuid,
            payload=update_req,
        )

        api_manager.user_steps.verify_person_updated(
            expected_update=update_req,
            actual_person_update = updated_person_response
        )


    @pytest.mark.usefixtures("api_manager", "created_person")
    def test_update_person_birthdate(self, api_manager, created_person):
        new_data = RandomModelGenerator.generate(CreatePersonRequest)
        update_req = UpdatePersonRequest(birthdate=new_data.birthdate)

        updated_person_response = api_manager.user_steps.update_person(
            person_uuid=created_person.uuid,
            payload=update_req,
        )

        api_manager.user_steps.verify_person_updated(
            expected_update=update_req,
            actual_person_update=updated_person_response,
        )


