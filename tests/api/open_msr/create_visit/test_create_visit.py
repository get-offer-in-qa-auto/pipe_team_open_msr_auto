
import pytest

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_data import RandomData
from src.api.models.requests.create_visit_request import CreateVisitRequest, CreateVisitInvalidRequest
from src.api.utils.datetime_utils import now_iso_utc


@pytest.mark.api
class TestCreateVisit:

    def test_create_visit(self, api_manager: ApiManager, create_visit_request: CreateVisitRequest):
        api_manager.visit_steps.create_visit(create_visit_request)

    @pytest.mark.parametrize(
        "bad_patient",
        [None, "", "not-a-uuid", str(RandomData.get_uuid())],
    )
    def test_create_visit_invalid_patient_field(self, api_manager, patient_context: dict,
                                                visit_type_uuid: str, bad_patient):
        payload = CreateVisitInvalidRequest(
            patient=bad_patient,
            visitType=visit_type_uuid,
            startDatetime=now_iso_utc(),
            location=patient_context["location_uuid"],
        )

        api_manager.visit_steps.create_invalid_visit(payload=payload,
                                                     error_key="error",
                                                     error_value="Patient Id is required")
