
import pytest
from playwright.sync_api import expect, Page

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.comparison.model_assertions import ModelAssertions

from src.api.models.requests.create_person_request import CreatePersonRequest
from src.ui.mappers.person_ui_mapper import PersonUiMapper
from src.ui.open_msr_home_page import OpenMsrHomePage
from src.ui.patient_pages.patient_create_page import PatientCreatePage
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage


@pytest.mark.ui
class TestCreatePatientByAdminUser:
    @pytest.mark.admin_session
    def test_add_patient_with_correct_data(
            self,
            page: Page,
            api_manager: ApiManager,
    ):
        person_request = RandomModelGenerator.generate(CreatePersonRequest)
        ui_data = PersonUiMapper.from_request(person_request)

        home = OpenMsrHomePage(page).open()

        patient_summary_page = (
            home
            .click_add_patient()
            .get_page(PatientCreatePage)
            .fill_basic_info(
                given=ui_data.given,
                family=ui_data.family,
                gender=ui_data.gender,
                age=ui_data.age,
            )
            .submit()
            .get_page(PatientSummaryPage)
            .should_be_opened()
        )

        expect(patient_summary_page.patient_name).to_contain_text(
            f"{ui_data.given} {ui_data.family}"
        )

        patient_uuid = patient_summary_page.get_patient_uuid()
        person_full = api_manager.user_steps.get_person_full(patient_uuid)

        patient_uuid = patient_summary_page.get_patient_uuid()
        person_full = api_manager.user_steps.get_person_full(patient_uuid)

        ModelAssertions(person_request, person_full).match()




