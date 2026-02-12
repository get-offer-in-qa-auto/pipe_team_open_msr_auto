import random

from src.api.models.contexts.patient_context import PatientContext
from src.api.utils.datetime_utils import now_iso_utc

import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.requests.create_visit_request import CreateVisitRequest
from src.api.models.responses.create_patient_response import PatientCreateResponse


@pytest.fixture
def api_manager(created_objects) -> ApiManager:
    return ApiManager(created_objects)


@pytest.fixture
def created_patient(api_manager: ApiManager) -> PatientCreateResponse:
    """Create a fresh patient (person + patient) for tests.

    The created objects are automatically registered in created_objects and removed in teardown.
    """
    return api_manager.user_steps.create_patient_from_existing_person()


@pytest.fixture
def create_visit_request(api_manager: ApiManager, created_patient: PatientCreateResponse) -> CreateVisitRequest:
    """Build a minimal valid request for POST /visit.

    Takes the first available Location and Visit Type.
    """
    visit_types = api_manager.user_steps.get_visit_types()
    visit_type_uuid = random.choice(visit_types.results).uuid

    locations = api_manager.user_steps.get_locations()
    location_uuid = random.choice(locations.results).uuid

    start_dt = now_iso_utc()

    return CreateVisitRequest(
        patient=created_patient.uuid,
        visitType=visit_type_uuid,
        startDatetime=start_dt,
        location=location_uuid,
        indication=None,
        encounters=None,
    )


@pytest.fixture
def visit_type_uuid(api_manager) -> str:
    visit_types = api_manager.user_steps.get_visit_types()
    return visit_types.results[0].uuid


@pytest.fixture
def patient_context(api_manager, created_patient) -> PatientContext:
    locations = api_manager.user_steps.get_locations()
    return PatientContext(
        patient_uuid=created_patient.uuid,
        location_uuid=locations.results[0].uuid,
    )