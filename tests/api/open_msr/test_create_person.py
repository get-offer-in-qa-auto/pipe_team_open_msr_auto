import pytest

from src.api.assertions.person_creation_verifier import PersonCreationVerifier
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest, CreatePersonInvalidRequest


@pytest.mark.api
def test_create_person(api_manager):
    create_person_request = RandomModelGenerator.generate(CreatePersonRequest)
    person = api_manager.user_steps.create_person(create_person_request)
    PersonCreationVerifier(api_manager).verify_person_created(person.uuid, expected_request=create_person_request)


#@pytest.mark.xfail #TODO: how fail by parametrized test
@pytest.mark.api
@pytest.mark.parametrize(
    "field, value, error_key, error_value",
    [
        (
            "gender","X",  # invalid (дока: M/F/U)
            "error",
            "gender",
        ),
    ],
)
def test_create_person_invalid(api_manager, field, value, error_key, error_value):
    create_person_request = RandomModelGenerator.generate(CreatePersonRequest)
    setattr(create_person_request, field, value)

    api_manager.user_steps.create_invalid_person(
        create_person_request=create_person_request,
        error_key=error_key,
        error_value=error_value,
    )
    #TODO: проверяем что персон не создался