import allure
import pytest

from src.api.classes.api_manager import ApiManager
from src.api.constants.error_keys import ErrorKeys
from src.api.constants.error_messages import ErrorMessages
from src.api.generators.random_data import RandomData
from src.api.models.requests.create_visit_request import CreateVisitRequest, CreateVisitInvalidRequest
from src.api.models.requests.update_visit_request import UpdateVisitRequest
from src.api.utils.datetime_utils import now_iso_utc


@pytest.mark.api
class TestCreateVisit:

    @allure.title("Create Visit")
    @pytest.mark.check_visit_persisted(expected_count=1)
    @allure.step("test_create_visit")
    def test_create_visit(self, api_manager: ApiManager, create_visit_request: CreateVisitRequest):
        api_manager.visit_steps.create_visit(create_visit_request)

    @pytest.mark.check_visit_not_created
    @pytest.mark.parametrize(
        "field_name, incorrect_value, expected_error",
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
        ]
    )
    @allure.title("Create Visit Invalid Required Fields")
    @allure.step("test_create_visit_invalid_required_fields")
    def test_create_visit_invalid_required_fields(self, api_manager, patient_context, visit_type_uuid: str,
                                                  field_name: str, incorrect_value, expected_error: str):
        payload = CreateVisitInvalidRequest(
            patient=patient_context.patient_uuid,
            visitType=visit_type_uuid,
            startDatetime=now_iso_utc(),
            location=patient_context.location_uuid,
        )

        setattr(payload, field_name, incorrect_value)

        api_manager.visit_steps.create_raw_visit(
            payload=payload,
            error_key=ErrorKeys.ERROR_KEY,
            error_value=expected_error,
        )

    @allure.title("Create Visit With Another Active Visit")
    @pytest.mark.check_visit_persisted(expected_count=1)
    @allure.step("test_create_visit_with_another_active_visit")
    def test_create_visit_with_another_active_visit(self, api_manager: ApiManager,
                                                    create_visit_request: CreateVisitRequest):
        api_manager.visit_steps.create_visit(create_visit_request)
        api_manager.visit_steps.create_raw_visit(create_visit_request, ErrorKeys.ERROR_KEY,
                                                 ErrorMessages.VISIT_OVERLAPS)

    @pytest.mark.check_visit_persisted(
        expected_count=2,
        request_source=("create_visit_request_with_stop_time", "create_visit_request"))
    @allure.title("Create Visit With Another Ended Visit")
    @allure.step("test_create_visit_with_another_ended_visit")
    def test_create_visit_with_another_ended_visit(self, api_manager: ApiManager,
                                                   create_visit_request: CreateVisitRequest,
                                                   create_visit_request_with_stop_time: CreateVisitRequest):
        api_manager.visit_steps.create_visit(create_visit_request_with_stop_time)
        api_manager.visit_steps.create_visit(create_visit_request)

    @allure.title("Delete Active Visit")
    @pytest.mark.check_visit_deleted
    @allure.step("test_delete_active_visit")
    def test_delete_active_visit(self, api_manager: ApiManager, create_visit_request: CreateVisitRequest):
        created = api_manager.visit_steps.create_visit(create_visit_request)
        api_manager.visit_steps.delete_visit(created.uuid)

    @allure.title("Update Active Visit")
    @pytest.mark.check_visit_updated
    @allure.step("test_update_active_visit")
    def test_update_active_visit(self, api_manager: ApiManager, create_visit_request: CreateVisitRequest,
                                 update_visit_request: UpdateVisitRequest):
        created = api_manager.visit_steps.create_visit(create_visit_request)
        api_manager.visit_steps.update_visit(created.uuid, update_visit_request)

    @pytest.mark.parametrize(
        "bad_stop_datetime",
        [
            "",
            RandomData.get_string(20),
            RandomData.get_bad_dt(),
            RandomData.get_bad_iso_utc_string(),
            RandomData.get_impossible_iso_utc()
        ])
    @allure.title("Update Visit Invalid Stop Datetime")
    @allure.step("test_update_visit_invalid_stop_datetime")
    def test_update_visit_invalid_stop_datetime(self, api_manager, create_visit_request, bad_stop_datetime):
        created = api_manager.visit_steps.create_visit(create_visit_request)

        payload = UpdateVisitRequest(stopDatetime=bad_stop_datetime)

        api_manager.visit_steps.update_invalid_visit(
            visit_uuid=created.uuid,
            payload=payload,
            error_key=ErrorKeys.ERROR_KEY,
            error_value=ErrorMessages.START_DATETIME_HAS_INVALID_FORMAT
        )
