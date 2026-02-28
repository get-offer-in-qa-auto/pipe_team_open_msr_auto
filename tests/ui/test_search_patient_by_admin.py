import re

import pytest
from playwright.sync_api import expect, Page

from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_patient_request import CreatePatientRequest
from src.api.models.responses.create_patient_response import PatientCreateResponse

from src.ui.open_msr_home_page import OpenMsrHomePage
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage


@pytest.mark.ui
@pytest.mark.usefixtures("admin_session_autologin")
@pytest.mark.admin_session
class TestSearchPatientByAdmin:

    #  Search by Fullname
    def test_search_patient_by_fullname_by_admin(
        self,
        page: Page,
        api_manager: ApiManager,
        created_objects
    ):

        request = api_manager.user_steps.build_create_patient_request()
        response = api_manager.user_steps.create_patient(request)

        given = request.person.names[0].givenName
        family = request.person.names[0].familyName
        full_name = f"{given} {family}"

        home_page = OpenMsrHomePage(page).open().wait_until_loaded()

        home_page.header_search \
            .open_search() \
            .search(full_name) \
            .should_have_result(full_name) \
            .select_first_result()

        expect(page).to_have_url(
            re.compile(rf"/patient/{response.uuid}/chart")
        )
        PatientSummaryPage(page, patient_uuid=response.uuid) \
            .should_be_opened() \
            .should_have_patient(given, family)



    #  Search by Identifier
    def test_search_patient_by_id_by_admin(
        self,
        page: Page,
        api_manager
    ):
        # --- Create patient ---
        request = api_manager.user_steps.build_create_patient_request()
        response = api_manager.user_steps.create_patient(request)

        identifier = request.identifiers[0].identifier

        # --- Search by ID ---
        OpenMsrHomePage(page).open().wait_until_loaded() \
            .header_search \
            .open_search() \
            .search(identifier) \
            .select_first_result()

        # --- Verify redirect ---
        expect(page).to_have_url(
            re.compile(rf"/patient/{response.uuid}/chart")
        )

        PatientSummaryPage(page, patient_uuid=response.uuid) \
            .should_be_opened()

    #  Search non-existent patient
    def test_search_patient_by_nonexistent_fullname_by_admin(
        self,
        page: Page,
    ):
        fake_name = "ZZZ Nonexistent Patient"

        home = OpenMsrHomePage(page).open().wait_until_loaded()

        search_component = home.header_search \
            .open_search() \
            .search(fake_name)

        search_component.should_have_no_results()