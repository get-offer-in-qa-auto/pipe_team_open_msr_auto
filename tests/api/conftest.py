from src.api.fixtures.user_fixtures import *
from src.api.fixtures.api_fixtures import *
from src.api.fixtures.objects_fixture import *
from src.api.generators.generator_context import GeneratorContext
import pytest


@pytest.fixture
def created_patient(api_manager):
    created = []

    yield created

    # teardown
    for patient_uuid in created:
        api_manager.user_steps.delete_patient(patient_uuid)

@pytest.fixture(autouse=True)
def inject_api_manager(api_manager):
    GeneratorContext.reference_provider = api_manager.reference_provider





