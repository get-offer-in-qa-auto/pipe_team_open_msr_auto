import pytest

from src.api.assertions.person_creation_verifier import PersonCreationVerifier
from src.api.generators.random_data import RandomData
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest, CreatePersonInvalidRequest


@pytest.mark.api
def test_create_person(api_manager):
    create_person_request = RandomModelGenerator.generate(CreatePersonRequest)
    person = api_manager.user_steps.create_person(create_person_request)
    PersonCreationVerifier(api_manager).verify_person_created(
        person.uuid,
        expected_request=create_person_request,
    )


@pytest.mark.api
@pytest.mark.parametrize(
    "field, value, error_value",
    [
        # ---------- birthdate ----------
        ("birthdate", "1997-99-99", "birth"),  # invalid date
        ("birthdate", "1997-02-30", "birth"),  # non-existing date
        ("birthdate", "abcd-ef-gh", "birth"),  # not a date
        ("birthdate", "", "birth"),            # empty
        ("birthdate", "3000-01-01", "birth"),  # future date
        ("birthdate", RandomData.get_int(1, 1000), "birth"),

        # ---------- addresses ----------
        ("addresses", RandomData.get_word(), "address"),  # wrong type
        ("addresses", None, "address"),  # null instead of array
        ("addresses", [{"address1": RandomData.get_int(1, 1000)}], "address"),
        ("addresses", [{"postalCode": RandomData.get_int(1, 1000)}], "address"),
        ("addresses", [{"cityVillage": RandomData.get_int(1, 1000)}], "address"),
        ("addresses", [{"country": RandomData.get_int(1, 1000)}], "address"),
        (
            "addresses",
            [{"address1": RandomData.get_word()}, RandomData.get_word()],
            "address",
        ),  # garbage in array

        # ---------- names ----------
        ("names", [], "name"),  # empty list
        ("names", None, "name"),  # null instead of array
        ("names", RandomData.get_word(), "name"),  # wrong type
        ("names", [{}], "name"),  # missing givenName/familyName
        ("names", [{"familyName": RandomData.get_word()}], "name"),  # missing givenName
        ("names", [{"givenName": "", "familyName": RandomData.get_word()}], "name"),
        ("names", [{"givenName": None, "familyName": RandomData.get_word()}], "name"),
        (
            "names",
            [{"givenName": RandomData.get_int(1, 1000), "familyName": RandomData.get_word()}],
            "name",
        ),
        (
            "names",
            [{"givenName": RandomData.get_word(), "familyName": RandomData.get_int(1, 1000)}],
            "name",
        ),
        (
            "names",
            [
                {"givenName": RandomData.get_word(), "familyName": RandomData.get_word()},
                RandomData.get_word(),
            ],
            "name",
        ),  # garbage in array
    ],
)
def test_create_person_invalid(api_manager, field, value, error_value):
    create_person_request = RandomModelGenerator.generate(CreatePersonRequest)

    setattr(create_person_request, field, value)

    api_manager.user_steps.create_invalid_person(
        create_person_request=create_person_request,
        error_value=error_value,
    )



    #TODO: проверяем что персон не создался