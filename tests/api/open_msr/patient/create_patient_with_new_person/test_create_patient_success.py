import pytest

from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_patient_request import CreatePatientRequest

@pytest.mark.api
def test_create_patient_success(api_manager, created_patient):
    """
    Happy path
    Contract: POST /patient must create patient when valid data provided.
    """

    request = RandomModelGenerator.generate(CreatePatientRequest)

    patient = api_manager.user_steps.create_patient(request)
    created_patient.append(patient.uuid)

    # GET verification
    patient_full = api_manager.user_steps.get_patient_full(patient.uuid)

    # Business assertions
    assert patient_full.person.gender == request.person.gender
