import pytest

from src.api.classes.api_manager import ApiManager
from src.api.constants.error_messages import ErrorMessages
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.generators.random_data import RandomData
from src.api.models.requests.create_patient_request import CreatePatientRequest
from src.api.specs.response_spec import ResponseSpecs


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
        request = RandomModelGenerator.generate(CreatePatientRequest)

        patient = api_manager.user_steps.create_patient(request)

        api_manager.user_steps.get_patient_full(patient.uuid)
        api_manager.database_steps.verify_patient_created_with_new_person(
            patient_uuid=patient.uuid,
            expected_request=request
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
        user_request, _ = create_user_with_roles(role_names=[role])

        request = RandomModelGenerator.generate(CreatePatientRequest)

        patient = api_manager.user_steps.create_patient(
            patient_request=request,
            user_request=user_request
        )

        api_manager.database_steps.verify_patient_created(patient.uuid)

    # --------------------------------------------------
    # Forbidden roles
    # --------------------------------------------------

    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    @pytest.mark.usefixtures("create_user_with_roles")
    @pytest.mark.parametrize("role", [
        "Organizational: Doctor",
        "Organizational: Nurse",
    ])
    def test_create_patient_with_new_person_forbidden_roles(
        self,
        api_manager,
        create_user_with_roles,
        role
    ):
        user_request, _ = create_user_with_roles(role_names=[role])

        request = RandomModelGenerator.generate(CreatePatientRequest)

        api_manager.user_steps.create_patient_invalid_request(
            patient_request=request,
            user_request=user_request,
            response_spec=ResponseSpecs.request_returns_forbidden()
        )

    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    @pytest.mark.usefixtures("create_user_with_roles")
    def test_create_patient_with_new_person_disabled_user(
            self,
            api_manager,
            create_user_with_roles
    ):
        user_request, user_data = create_user_with_roles()

        # disable user
        api_manager.user_steps.delete_user(user_data.uuid, purge=False)

        request = RandomModelGenerator.generate(CreatePatientRequest)

        # ✅ сохраняем identity ДО вызова API
        original_identifier = request.identifiers[0].identifier
        original_given_name = request.person.names[0].givenName
        original_family_name = request.person.names[0].familyName
        original_birthdate = request.person.birthdate

        api_manager.user_steps.create_patient_invalid_request(
            patient_request=request,
            user_request=user_request,
            response_spec=ResponseSpecs.request_returns_unauthorized_with_message(
                ErrorMessages.USER_IS_NOT_LOGGED_IN
            )
        )

        # verify patient not created
        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

        # verify person not created (rollback check)
        api_manager.database_steps.verify_person_not_created_by_identity(
            given_name=original_given_name,
            family_name=original_family_name,
            birthdate=original_birthdate
        )

    # invalid person root field
    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    def test_create_patient_missing_person(self, api_manager):
        request = RandomModelGenerator.generate(CreatePatientRequest)

        del request.person

        api_manager.user_steps.create_patient_invalid_data(request)

        api_manager.database_steps.verify_patient_not_created()

    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    def test_create_patient_rollback_on_invalid_identifier(self, api_manager):
        request = RandomModelGenerator.generate(CreatePatientRequest)

        original_identifier = request.identifiers[0].identifier
        original_given_name = request.person.names[0].givenName
        original_family_name = request.person.names[0].familyName
        original_birthdate = request.person.birthdate

        # ломаем identifier
        request.identifiers[0].identifier = ""

        api_manager.user_steps.create_patient_invalid_data(request)

        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

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
            # ---------- identifierType ----------
            ("identifierType", "", ErrorMessages.EMPTY_IDENTIFIER_TYPE),
            ("identifierType", None, ErrorMessages.EMPTY_IDENTIFIER_TYPE),
            ("identifierType", RandomData.get_int(1, 1000), ErrorMessages.INT_IDENTIFIER_TYPE),
            ("identifierType", RandomData.get_word(), ErrorMessages.EMPTY_IDENTIFIER_TYPE),
            ("identifierType", str(RandomData.get_uuid()), ErrorMessages.EMPTY_IDENTIFIER_TYPE),

            # ---------- location ----------
            ("location", "", ErrorMessages.EMPTY_LOCATION),
            ("location", None, ErrorMessages.EMPTY_LOCATION),
            ("location", RandomData.get_int(1, 1000), ErrorMessages.INT_LOCATION),
            ("location", RandomData.get_word(), ErrorMessages.EMPTY_LOCATION),
            ("location", str(RandomData.get_uuid()), ErrorMessages.EMPTY_LOCATION),

            # ---------- identifier ----------
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
        request = RandomModelGenerator.generate(CreatePatientRequest)

        identifier = request.identifiers[0]

        # сохраняем оригинальные значения
        original_identifier = identifier.identifier
        person_birthdate = request.person.birthdate

        setattr(identifier, field, value)

        api_manager.user_steps.create_patient_invalid_data(
            patient_request=request,
            error_message=error_message
        )

        # verify patient not created
        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

        # verify person not created (rollback check)
        original_given_name = request.person.names[0].givenName
        original_family_name = request.person.names[0].familyName

        api_manager.database_steps.verify_person_not_created_by_identity(
            given_name=original_given_name,
            family_name=original_family_name,
            birthdate=person_birthdate
        )

    @pytest.mark.api
    @pytest.mark.check_all_patients_change(delta=0, should_exist=False)
    @pytest.mark.parametrize(
        "field, value, error_value",
        [
            # ---------- gender ----------
            ("gender", None, "gender"),
            ("gender", "", "gender"),
            ("gender", 123, "gender"),
            ("gender", "male", "gender"),
            ("gender", "XYZ", "gender"),

            # ---------- birthdate ----------
            ("birthdate", "1997-99-99", "birth"),
            ("birthdate", "1997-02-30", "birth"),
            ("birthdate", "abcd-ef-gh", "birth"),
            ("birthdate", "", "birth"),
            ("birthdate", "3000-01-01", "birth"),
            ("birthdate", RandomData.get_int(1, 1000), "birth"),

            # ---------- addresses ----------
            ("addresses", RandomData.get_word(), "address"),
            ("addresses", None, "address"),
            ("addresses", [{"address1": RandomData.get_int(1, 1000)}], "address"),
            ("addresses", [{"postalCode": RandomData.get_int(1, 1000)}], "address"),
            ("addresses", [{"cityVillage": RandomData.get_int(1, 1000)}], "address"),
            ("addresses", [{"country": RandomData.get_int(1, 1000)}], "address"),
            (
                    "addresses",
                    [{"address1": RandomData.get_word()}, RandomData.get_word()],
                    "address",
            ),

            # ---------- names ----------
            ("names", [], "name"),
            ("names", None, "name"),
            ("names", RandomData.get_word(), "name"),
            ("names", [{}], "name"),
            ("names", [{"familyName": RandomData.get_word()}], "name"),
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
            ),
        ],
    )
    def test_create_patient_with_new_person_invalid_nested_person(
            self,
            api_manager,
            field,
            value,
            error_value
    ):
        request = RandomModelGenerator.generate(CreatePatientRequest)

        original_identifier = request.identifiers[0].identifier
        original_given_name = request.person.names[0].givenName
        original_family_name = request.person.names[0].familyName
        original_birthdate = request.person.birthdate

        # ломаем nested person
        setattr(request.person, field, value)

        api_manager.user_steps.create_patient_invalid_data(
            patient_request=request,
            error_message=error_value
        )

        # patient не создан
        api_manager.database_steps.verify_patient_not_created_by_identifier(
            original_identifier
        )

        api_manager.database_steps.verify_person_not_created_by_identity(
            given_name=original_given_name,
            family_name=original_family_name,
            birthdate=original_birthdate
        )
