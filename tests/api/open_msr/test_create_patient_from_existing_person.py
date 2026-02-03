import pytest



@pytest.mark.api
def test_create_patient_from_existing_person(api_manager):
    api_manager.admin_steps.create_patient_from_existing_person()
