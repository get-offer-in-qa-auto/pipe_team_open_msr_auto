import allure
import pytest

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.requests.update_person_request import UpdatePersonRequest



@pytest.mark.api
class TestUpdatePerson:
    @allure.title("Update Person Gender")
    @pytest.mark.usefixtures('api_manager', 'created_person')
    @allure.step("test_update_person_gender")
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


    @allure.title("Update Person Birthdate")
    @pytest.mark.usefixtures("api_manager", "created_person")
    @allure.step("test_update_person_birthdate")
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

    @pytest.mark.parametrize(
        "field, value, error_value",
        [
            ("birthdate", "1997-99-99", "birth"),   # invalid date
            ("birthdate", "1997-02-30", "birth"),   # non-existing date
            ("birthdate", "abcd-ef-gh", "birth"),   # not a date
            ("birthdate", "", "birth"),             # empty
        ],
    )
    @allure.title("Update Person Invalid")
    @allure.step("test_update_person_invalid")
    def test_update_person_invalid(self, api_manager, created_person, field, value, error_value):
        before = api_manager.user_steps.get_person_full(created_person.uuid)

        update_req = UpdatePersonRequest()
        setattr(update_req, field, value)

        api_manager.user_steps.update_person_invalid(
            person_uuid=created_person.uuid,
            update_person_request=update_req,
            error_value=error_value,
        )

        after = api_manager.user_steps.get_person_full(created_person.uuid)
        api_manager.user_steps.verify_person_not_changed(before, after)




