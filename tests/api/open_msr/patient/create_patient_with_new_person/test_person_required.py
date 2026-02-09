import pytest

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_patient_request import CreatePatientRequest

# Contract: POST /patient (create patient with NEW person)
#
# Field: person
# Requirement: REQUIRED
# Type: object (PatientPerson)
# API must reject request when:
# - person is null
# - person has invalid type
# - person is missing
# We verify ONLY that request is rejected (not error message text).

@pytest.mark.api
class TestCreatePatientPersonRequired:
    @pytest.mark.parametrize("person_value", [
        None,
        "",
        "some-string",
        123,
        [],
        {}
    ])
    def test_create_patient_person_invalid(self, api_manager, person_value):
        request = RandomModelGenerator.generate(CreatePatientRequest)

        # Break root field contract
        request.person = person_value

        api_manager.user_steps.create_patient_invalid_data(request)

    def test_create_patient_person_missing(self, api_manager):
        request = RandomModelGenerator.generate(CreatePatientRequest)

        # Remove field completely from payload
        del request.person

        api_manager.user_steps.create_patient_invalid_data(request)
