import allure
import pytest
from playwright.sync_api import Page

from src.api.classes.api_manager import ApiManager
from src.api.models.responses.create_visit_response import CreateVisitResponse
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage


@pytest.mark.ui
@pytest.mark.usefixtures("admin_session_autologin")
@pytest.mark.admin_session
class TestVisitActions:

    PUNCTUALITY_ON_TIME = "On time"
    FACILITY_VISIT = "Facility Visit"

    @allure.title("Create Visit For Patient")
    @pytest.mark.check_visit_created_in_db
    def test_create_visit_for_patient(self, page: Page, api_manager: ApiManager, created_patient):
        PatientSummaryPage(page, patient_uuid=created_patient.uuid).open()\
            .open_actions() \
            .click_add_visit() \
            .select_visit_type(self.FACILITY_VISIT) \
            .set_punctuality(self.PUNCTUALITY_ON_TIME) \
            .click_start_visit() \
            .should_have_active_visit() \
            .should_have_punctuality(self.PUNCTUALITY_ON_TIME)

    @allure.title("End Visit")
    @pytest.mark.check_visit_db_state(visit_fixture="created_visit", ended=True)
    def test_end_visit(self, page, created_visit: CreateVisitResponse):
        PatientSummaryPage(page, patient_uuid=created_visit.patient.uuid).open()\
            .should_be_opened() \
            .should_have_active_visit() \
            .open_actions() \
            .click_end_active_visit() \
            .confirm_end_visit() \
            .should_not_have_active_visit()

    @allure.title("Delete Visit")
    @pytest.mark.check_visit_db_state(visit_fixture="created_visit", voided=True)
    def test_delete_visit(self, page, created_visit: CreateVisitResponse):
        PatientSummaryPage(page, patient_uuid=created_visit.patient.uuid).open()\
            .should_be_opened() \
            .should_have_active_visit() \
            .open_actions() \
            .click_delete_active_visit() \
            .confirm_delete_visit() \
            .should_not_have_active_visit()

    @allure.title("Cancel End Visit")
    @pytest.mark.check_visit_db_state(visit_fixture="created_visit", ended=False)
    def test_cancel_end_visit(self, page, created_visit: CreateVisitResponse):
        PatientSummaryPage(page, patient_uuid=created_visit.patient.uuid).open() \
            .should_be_opened() \
            .should_have_active_visit() \
            .open_actions() \
            .click_end_active_visit() \
            .cancel_end_visit() \
            .should_have_active_visit()