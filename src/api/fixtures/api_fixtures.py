from __future__ import annotations

from datetime import datetime, timezone
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
    return api_manager.admin_steps.create_patient_from_existing_person()


@pytest.fixture
def create_visit_request(api_manager: ApiManager, created_patient: PatientCreateResponse) -> CreateVisitRequest:
    """Build a minimal valid request for POST /visit.

    Takes the first available Location and Visit Type.
    """
    visit_types = api_manager.admin_steps.get_visit_types()
    visit_type_uuid = visit_types.results[0].uuid

    locations = api_manager.admin_steps.get_locations()
    location_uuid = locations.results[0].uuid

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
def valid_visit_payload(api_manager, created_patient):
    visit_types = api_manager.admin_steps.get_visit_types()
    locations = api_manager.admin_steps.get_locations()

    start_dt = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    return {
        "patient": created_patient.uuid,
        "visitType": visit_types.results[0].uuid,
        "startDatetime": start_dt,
        "location": locations.results[0].uuid,
        # optional:
        # "indication": "some text",
        # "encounters": [],
    }


@pytest.fixture
def visit_type_uuid(api_manager) -> str:
    visit_types = api_manager.admin_steps.get_visit_types()
    return visit_types.results[0].uuid


@pytest.fixture
def patient_context(api_manager, created_patient) -> dict:
    locations = api_manager.admin_steps.get_locations()
    return {
        "patient_uuid": created_patient.uuid,
        "location_uuid": locations.results[0].uuid,
    }