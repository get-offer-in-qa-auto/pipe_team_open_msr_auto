
import pytest
from playwright.sync_api import Page

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.comparison.model_assertions import ModelAssertions

from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.responses.create_patient_response import PatientCreateResponse
from src.ui.login_pages.login_page import LoginPage
from src.ui.mappers.person_ui_mapper import PersonUiMapper
from src.ui.open_msr_home_page import OpenMsrHomePage
from src.ui.patient_pages.patient_create_page import PatientCreatePage
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage


@pytest.mark.ui
class TestCreatePatientByUser:
    @pytest.mark.usefixtures("user_session_extension")
    @pytest.mark.user_session(1)
    def test_add_patient_with_correct_data(
            self,
            page: Page,
            created_objects,
            api_manager: ApiManager,
    ):
        person_request = RandomModelGenerator.generate(CreatePersonRequest)
        ui_data = PersonUiMapper.from_request(person_request)

        patient_summary_page = (
            OpenMsrHomePage(page)
            .open()
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
            .should_have_patient(ui_data.given, ui_data.family)
        )

        patient_uuid = patient_summary_page.get_patient_uuid_from_summery_page()
        person_full = api_manager.user_steps.get_person_full(patient_uuid)
        created_objects.append(PatientCreateResponse(uuid=patient_uuid))

        ModelAssertions(person_request, person_full).match()

    @pytest.mark.usefixtures('api_manager', 'created_person', 'create_user_with_roles')
    @pytest.mark.parametrize('role', [
        "Privilege Level: High",
        "Organizational: Doctor",
    ])
    def test_add_patient_user_has_allowed_roles_to_create_patient(
            self,
            page: Page,
            created_objects,
            api_manager: ApiManager,
            create_user_with_roles,
            role
    ):
        user_request, _ = create_user_with_roles([role])
        LoginPage(page).auth_as_user(user_request)

        # объедениь
        person_request = RandomModelGenerator.generate(CreatePersonRequest)
        ui_data = PersonUiMapper.from_request(person_request)

        patient_summary_page = (
            OpenMsrHomePage(page)
            .open()
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
            .should_have_patient(ui_data.given, ui_data.family)
        )

        patient_uuid = patient_summary_page.get_patient_uuid_from_summery_page()
        person_full = api_manager.user_steps.get_person_full(patient_uuid)
        created_objects.append(PatientCreateResponse(uuid=patient_uuid))

        ModelAssertions(person_request, person_full).match()

    @pytest.mark.usefixtures('api_manager', 'create_user_with_privileges')
    def test_create_patient_no_create_edit_patient_privilege_user(self, api_manager, page,
                                                                  create_user_with_privileges):
        exclude_privilege_names = ['Add Patients', 'Edit Patients']
        user_request, _ = create_user_with_privileges(exclude_privilege_names=exclude_privilege_names)
        LoginPage(page).auth_as_user(user_request)

        person_request = RandomModelGenerator.generate(CreatePersonRequest)
        ui_data = PersonUiMapper.from_request(person_request)

        OpenMsrHomePage(page)\
            .open()\
            .click_add_patient()\
            .get_page(PatientCreatePage)\
            .fill_basic_info(
                given=ui_data.given,
                family=ui_data.family,
                gender=ui_data.gender,
                age=ui_data.age,
            )\
            .submit()\
            .should_be_opened()

        person_dao = api_manager.database_steps.find_person_name_by_given_and_last_name(ui_data.given, ui_data.family)
        assert person_dao is None,\
            f"Person with name '{ui_data.given} {ui_data.family}' should NOT exist in DB after invalid create, but was found: {person_dao}"
