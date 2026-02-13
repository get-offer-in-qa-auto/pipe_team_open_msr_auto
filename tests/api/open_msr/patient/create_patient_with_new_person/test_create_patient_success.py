import pytest

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.comparison.model_assertions import ModelAssertions
from src.api.models.requests.create_patient_request import CreatePatientRequest
import json

from tests.api.open_msr import patient



@pytest.mark.api
def test_create_patient_success(api_manager):
    """
    Contract: POST /patient must create patient when valid data provided.
    Response must match request payload.
    """

    request = RandomModelGenerator.generate(CreatePatientRequest)

    patient = api_manager.user_steps.create_patient(request)

    assert patient.uuid is not None

    ModelAssertions(request, patient).match()

    print(json.dumps(patient.model_dump(), indent=2, ensure_ascii=False))
