
import pytest

from src.api.classes.api_manager import ApiManager
from src.api.constants.error_keys import ErrorKeys
from src.api.constants.error_messages import ErrorMessages
from src.api.generators.random_data import RandomData
from src.api.models.requests.create_visit_request import CreateVisitRequest, CreateVisitInvalidRequest
from src.api.utils.datetime_utils import now_iso_utc


@pytest.mark.api
class TestCreateVisit:

    @pytest.mark.check_visit_persisted(expected_count=1)
    def test_create_visit(self, api_manager: ApiManager, create_visit_request: CreateVisitRequest):
        api_manager.visit_steps.create_visit(create_visit_request)

    @pytest.mark.check_visit_not_created(expected_count=0)
    @pytest.mark.parametrize(
        "field_name,bad_value,expected_error",
        [
            ("patient", None, ErrorMessages.PATIENT_ID_IS_REQUIRED),
            ("patient", "", ErrorMessages.PATIENT_ID_IS_REQUIRED),
            ("patient", RandomData.get_string(10), ErrorMessages.PATIENT_ID_IS_REQUIRED),
            ("patient", RandomData.get_uuid(), ErrorMessages.PATIENT_ID_IS_REQUIRED),

            ("visitType", None, ErrorMessages.VISIT_TYPE_IS_REQUIRED),
            ("visitType", "", ErrorMessages.VISIT_TYPE_IS_REQUIRED),
            ("visitType", RandomData.get_string(10), ErrorMessages.VISIT_TYPE_IS_REQUIRED),
            ("visitType", RandomData.get_uuid(), ErrorMessages.VISIT_TYPE_IS_REQUIRED),

            ("startDatetime", RandomData.get_bad_dt(), ErrorMessages.START_DATETIME_HAS_INVALID_FORMAT),
            ("startDatetime", "", ErrorMessages.START_DATETIME_HAS_INVALID_FORMAT),
            ("startDatetime", RandomData.get_string(30), ErrorMessages.START_DATETIME_HAS_INVALID_FORMAT),
        ],
        ids=lambda x: str(x),
    )
    def test_create_visit_invalid_required_fields(self, api_manager, patient_context, visit_type_uuid: str,
                                                  field_name: str, bad_value, expected_error: str):
        payload = CreateVisitInvalidRequest(
            patient=patient_context.patient_uuid,
            visitType=visit_type_uuid,
            startDatetime=now_iso_utc(),
            location=patient_context.location_uuid,
        )

        setattr(payload, field_name, bad_value)

        api_manager.visit_steps.create_invalid_visit(
            payload=payload,
            error_key=ErrorKeys.ERROR_KEY,
            error_value=expected_error,
        )