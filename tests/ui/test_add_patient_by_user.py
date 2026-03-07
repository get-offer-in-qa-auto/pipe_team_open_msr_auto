import logging

import allure
import pytest
from playwright.sync_api import Page

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.comparison.model_assertions import ModelAssertions
from src.ui.login_pages.login_page import LoginPage
from src.ui.models.create_person_ui_model import CreatePersonUi
from src.ui.open_msr_home_page import OpenMsrHomePage
from src.ui.patient_pages.patient_create_page import PatientCreatePage
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage

logger = logging.getLogger(__name__)


@pytest.mark.ui
class TestCreatePatientByUser:
    @allure.title("Create patient with valid data")
    @pytest.mark.usefixtures("user_session_extension")
    @pytest.mark.user_session(1)
    def test_add_patient_with_correct_data(
        self,
        page: Page,
        created_objects,
        api_manager: ApiManager,
    ):
        ui_data = RandomModelGenerator.generate(CreatePersonUi)
        logger.info(
            "Creating patient by regular user with generated data: given=%s, family=%s, gender=%s, age=%s",
            ui_data.given,
            ui_data.family,
            ui_data.gender,
            ui_data.age,
        )

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
            .register_created_patient(created_objects) \
            .call_api(api_manager.user_steps.get_person_full)

        logger.info("Comparing UI data with person returned by API")
        ModelAssertions(ui_data, person_full).match()
        logger.info("Patient creation by regular user validated successfully")

    @allure.title("Create patient by user with role: {role}")
    @pytest.mark.usefixtures('api_manager', 'created_person', 'create_user_with_roles')
    @pytest.mark.parametrize('role', [
        "Privilege Level: High",
        "Organizational: Doctor",
    ])
    def test_add_patient_user_has_allowed_roles_to_create_patient(
        self, page: Page, created_objects, api_manager: ApiManager, create_user_with_roles, role
    ):
        user_request, _ = create_user_with_roles([role])
        logger.info("Created user with role '%s' for patient creation test", role)

        # логинимся под созданным пользователем
        LoginPage(page).auth_as_user(user_request)
        logger.info("Authenticated as user '%s'", user_request.username)

        ui_data = RandomModelGenerator.generate(CreatePersonUi)
        logger.info(
            "Creating patient with allowed role '%s': given=%s, family=%s, gender=%s, age=%s",
            role,
            ui_data.given,
            ui_data.family,
            ui_data.gender,
            ui_data.age,
        )

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
            .register_created_patient(created_objects) \
            .call_api(api_manager.user_steps.get_person_full)

        logger.info("Comparing UI data with person returned by API for role '%s'", role)
        ModelAssertions(ui_data, person_full).match()
        logger.info("Patient creation with role '%s' validated successfully", role)

    @allure.title("User without Add/Edit Patients privilege cannot create patient")
    @pytest.mark.usefixtures('api_manager', 'create_user_with_privileges')
    def test_create_patient_no_create_edit_patient_privilege_user(self, api_manager, page, create_user_with_privileges):
        exclude_privilege_names = ['Add Patients', 'Edit Patients']
        user_request, _ = create_user_with_privileges(exclude_privilege_names=exclude_privilege_names)
        logger.info(
            "Created user without privileges %s to verify patient creation is blocked",
            exclude_privilege_names,
        )

        LoginPage(page).auth_as_user(user_request)
        logger.info("Authenticated as restricted user '%s'", user_request.username)

        ui_data = RandomModelGenerator.generate(CreatePersonUi)
        logger.info(
            "Attempting patient creation without required privileges: given=%s, family=%s, gender=%s, age=%s",
            ui_data.given,
            ui_data.family,
            ui_data.gender,
            ui_data.age,
        )

        OpenMsrHomePage(page) \
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
            .should_be_opened()

        person_dao = api_manager.database_steps.find_person_name_by_given_and_last_name(
            ui_data.given,
            ui_data.family,
        )
        logger.info("DB lookup result for blocked patient creation: %s", person_dao)

        assert person_dao is None, (
            f"Person with name '{ui_data.given} {ui_data.family}' "
            f"should NOT exist in DB after invalid create, but was found: {person_dao}"
        )
        logger.info("Verified patient was not created without required privileges")
