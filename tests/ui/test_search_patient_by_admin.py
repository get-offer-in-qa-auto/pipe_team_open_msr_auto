import pytest
from playwright.sync_api import Page

from src.api.models.requests.create_patient_request import CreatePatientRequest
from src.api.classes.api_manager import ApiManager
from src.api.generators.random_model_generator import RandomModelGenerator
from src.api.models.requests.create_person_request import CreatePersonRequest
from src.api.models.responses.create_patient_response import PatientCreateResponse
from src.api.models.comparison.model_assertions import ModelAssertions

from src.ui.mappers.person_ui_mapper import PersonUiMapper
from src.ui.open_msr_home_page import OpenMsrHomePage
from src.ui.patient_pages.patient_create_page import PatientCreatePage
from src.ui.patient_pages.patient_summery_page import PatientSummaryPage

@pytest.mark.ui
class TestSearchPatientByUser:

    @pytest.mark.usefixtures("user_session_extension")
    def test_search_existing_patient_by_name(
            self,
            page: Page,
            created_objects,
            api_manager: ApiManager,
    ):
        # -------- Arrange (API) --------
        patient_request = RandomModelGenerator.generate(CreatePatientRequest)
        created_patient = api_manager.user_steps.create_patient(patient_request)

        created_objects.append(created_patient)

        expected_name = created_patient.person.preferredName.display

        # -------- Act (UI Search) --------
        summary_page = (
            OpenMsrHomePage(page)
            .open()
            .header_search
            .search_and_open(created_patient.person.preferredName.givenName)
        )

        # -------- Assert (UI) --------
        summary_page \
            .should_be_opened() \
            .should_have_patient(
            created_patient.person.preferredName.givenName,
            created_patient.person.preferredName.familyName
        ) \
            .should_have_uuid(created_patient.uuid)

        # -------- Assert (API) --------
        person_full = api_manager.user_steps.get_person_full(created_patient.uuid)
        ModelAssertions(patient_request, person_full).match()