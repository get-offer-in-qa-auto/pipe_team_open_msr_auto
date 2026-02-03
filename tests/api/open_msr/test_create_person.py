import pytest


from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest, CreatePersonInvalidRequest


@pytest.mark.api
def test_create_person(api_manager):
    req = RandomModelGenerator.generate(CreatePersonRequest)
    created = api_manager.admin_steps.create_person(req)

    #TODO: убрать куда-нибудь
    assert created.uuid
    assert created.voided is False
    assert created.preferredName.uuid
    full = api_manager.admin_steps.get_person_full(created.uuid)

    # TODO: убрать куда-нибудь
    assert full.uuid == created.uuid


@pytest.mark.xfail #TODO: how fail by parametrized test
@pytest.mark.api
@pytest.mark.parametrize(
    "payload, error_key, error_value",
    [
        (
            CreatePersonInvalidRequest(
                names=[{"givenName": "John", "familyName": "Doe"}],
                gender="X",  # invalid (дока: M/F/U)
                birthdate="1997-09-02",
                addresses=[{"address1": "Street 1", "cityVillage": "City", "country": "CH", "postalCode": "8000"}],
            ),
            "error",
            "gender",
        ),
        (
            CreatePersonInvalidRequest(
                names=[{"givenName": "John", "familyName": "Doe"}],
                gender="M",
                birthdate="1997-99-99",  # invalid date
                addresses=[{"address1": "Street 1", "cityVillage": "City", "country": "CH", "postalCode": "8000"}],
            ),
            "error",
            "birth",
        ),
    ],
)
def test_create_person_invalid(api_manager, payload, error_key, error_value):
    api_manager.admin_steps.create_invalid_person(
        create_person_request=payload,
        error_key=error_key,
        error_value=error_value,
    )