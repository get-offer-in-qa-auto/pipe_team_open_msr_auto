
import allure
import pytest
from playwright.sync_api import Page

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.comparison.model_assertions import ModelAssertions

from src.ui.models.create_person_ui_model import CreatePersonUi
from src.ui.open_msr_home_page import OpenMsrHomePage
from src.ui.patient_pages.patient_create_page import PatientCreatePage
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage


@pytest.mark.ui
@pytest.mark.usefixtures("admin_session_autologin")
class TestCreatePatientByAdminUser:
    @allure.title("Add Patient With Correct Data")
    @pytest.mark.admin_session
    @allure.step("test_add_patient_with_correct_data")
    def test_add_patient_with_correct_data(
            self,
            page: Page,
            api_manager: ApiManager,
    ):
        ui_data = RandomModelGenerator.generate(CreatePersonUi)

        person_full = OpenMsrHomePage(page) \
            .open() \
            .click_add_patient() \
            .get_page(PatientCreatePage) \
            .fill_basic_info(
            given=ui_data.given,
            family=ui_data.family,
            gender=ui_data.gender,
            age=ui_data.age,
        ) \
            .submit() \
            .get_page(PatientSummaryPage) \
            .should_be_opened() \
            .should_have_patient(ui_data.given, ui_data.family) \
            .switch_to_api(api_manager) \
            .call_api(api_manager.user_steps.get_person_full)

        ModelAssertions(ui_data, person_full).match()




