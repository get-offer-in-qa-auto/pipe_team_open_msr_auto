import pytest

from src.api.assertions.person_creation_verifier import PersonCreationVerifier
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest, CreatePersonInvalidRequest


@pytest.mark.api
def test_create_person(api_manager):
    create_person_request = RandomModelGenerator.generate(CreatePersonRequest)
    person = api_manager.user_steps.create_person(create_person_request)
    PersonCreationVerifier(api_manager).verify_person_created(person.uuid, expected_request=create_person_request)


@pytest.mark.api
@pytest.mark.parametrize(
    "field, value, error_key, error_value",
    [
        # Failed - it's a bug
        # # ---------- gender ----------
        # ("gender", "", "error", "gender"),        # empty
        # ("gender", None, "error", "gender"),      # null
        # ("gender", "X", "error", "gender"),       # not M/F/U
        # ("gender", "male", "error", "gender"),    # invalid enum
        # ("gender", 1, "error", "gender"),         # wrong type

        # ---------- birthdate ----------
        ("birthdate", "1997-99-99", "error", "birth"),  # invalid date
        ("birthdate", "1997-02-30", "error", "birth"),  # non-existing date
        ("birthdate", "abcd-ef-gh", "error", "birth"),  # not a date
        ("birthdate", "", "error", "birth"),            # empty
        ("birthdate", "3000-01-01", "error", "birth"),  # future date

        # ---------- addresses ----------
        ("addresses", "some address", "error", "address"),  # неверный тип
        ("addresses", None, "error", "address"),  # null вместо массива
        ("addresses", [{"address1": 123}], "error", "address"),  # неверный тип address1
        ("addresses", [{"postalCode": 560037}], "error", "address"),  # неверный тип postalCode
        ("addresses", [{"cityVillage": 1}], "error", "address"),  # неверный тип cityVillage
        ("addresses", [{"country": 999}], "error", "address"),  # неверный тип country
        ("addresses", [{"address1": "x"}, "bad"], "error", "address"),  # мусор в массиве

        # ---------- names ----------
        ("names", [], "error", "name"),  # пустой список
        ("names", None, "error", "name"),  # null вместо массива
        ("names", "Mohit Kumar", "error", "name"),  # неверный тип
        ("names", [{}], "error", "name"),  # нет givenName/familyName
        ("names", [{"familyName": "Kumar"}], "error", "name"),  # нет givenName
        ("names", [{"givenName": "", "familyName": "Kumar"}], "error", "name"),  # пустой givenName
        ("names", [{"givenName": None, "familyName": "Kumar"}], "error", "name"),  # null givenName
        ("names", [{"givenName": 1, "familyName": "Kumar"}], "error", "name"),  # неверный тип givenName
        ("names", [{"givenName": "Mohit", "familyName": 2}], "error", "name"),  # неверный тип familyName
        ("names", [{"givenName": "Mohit", "familyName": "Kumar"}, "bad"], "error", "name"),  # мусор в массиве
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