import uuid

import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.comparison.entity_assertions import EntityAssertions
from src.api.models.requests.create_visit_request import CreateVisitRequest, CreateVisitInvalidRequest
from src.api.utils.datetime_utils import now_iso_utc


@pytest.mark.api
def test_create_visit(api_manager: ApiManager, create_visit_request: CreateVisitRequest):
    created_visit = api_manager.visit_steps.create_visit(create_visit_request)
    EntityAssertions.has_uuid(created_visit)


@pytest.mark.api
@pytest.mark.parametrize(
    "bad_patient",
    [None, "", "not-a-uuid", str(uuid.uuid4())],
)
def test_create_visit_invalid_patient_field(api_manager, patient_context: dict, visit_type_uuid: str, bad_patient):
    payload = CreateVisitInvalidRequest(
        patient=bad_patient,
        visitType=visit_type_uuid,
        startDatetime=now_iso_utc(),
        location=patient_context["location_uuid"],
    )

    api_manager.visit_steps.create_invalid_visit(payload=payload, error_key="error", error_value="Patient Id is required")
