from playwright.sync_api import Locator, expect
import re

from src.ui.base_page import BasePage


class PatientSummaryPage(BasePage):

    def __init__(self, page, patient_uuid: str | None = None):
        super().__init__(page)
        self.patient_uuid = patient_uuid

    # ---------- URL ----------

    def url(self) -> str:
        """
        Формирование URL страницы Patient Summary.

        /spa/patient/<uuid>/chart/Patient%20Summary
        """
        if not self.patient_uuid:
            raise ValueError(
                "patient_uuid must be provided to open PatientSummaryPage"
            )

        return f"/patient/{self.patient_uuid}/chart/Patient%20Summary"

    # ---------- Patient Banner ----------

    @property
    def openmrs_id(self):
        return self.page.locator("text=OpenMRS ID")

    @property
    def patient_banner(self):
        return self.page.locator('header[aria-label="patient banner"]')

    @property
    def actions_button(self):
        return self.page.get_by_role("button", name="Actions")

    def open_actions(self):
        self.actions_button.click()
        return self

    @property
    def active_visit(self):
        return self.patient_banner.get_by_title("Active Visit")

    def chosen_punctuality(self, punctuality_type: str):
        return self.patient_banner.get_by_title(punctuality_type)

    # ---------- Summary Sections ----------

    @property
    def vitals_section(self):
        return self.page.get_by_role("heading", name="Vitals")

    @property
    def biometrics_section(self):
        return self.page.get_by_role("heading", name="Biometrics")

    @property
    def conditions_section(self):
        return self.page.get_by_role("heading", name="Conditions")

    @property
    def medications_section(self):
        return self.page.get_by_role("heading", name="Active Medications")

    # ---------- Left Navigation ----------

    @property
    def patient_summary_nav(self):
        return self.page.get_by_role("link", name="Patient summary")

    @property
    def visits_nav(self):
        return self.page.get_by_role("link", name="Visits")

    @property
    def allergies_nav(self):
        return self.page.get_by_role("link", name="Allergies")

    # ------ Actions modal --------

    @property
    def add_visit_button(self):
        return self.page.get_by_role("menuitem", name="Add visit")

    @property
    def end_active_visit_button(self):
        return self.page.get_by_role("menuitem", name="End active visit")

    def click_add_visit(self):
        self.add_visit_button.click()
        return self

    def click_end_active_visit(self):
        self.end_active_visit_button.click()
        return self

    # ---Start visit modal --------

    @property
    def start_visit_form(self):
        return self.page.locator('[data-openmrs-role="Start Visit Form"]')

    @property
    def visit_type_group(self):
        return self.start_visit_form.locator("fieldset.cds--radio-button-group")

    def _radio_by_text(self, group: Locator, text: str):
        return group.locator("label.cds--radio-button__label", has_text=text)

    def select_visit_type(self, name: str):
        self._radio_by_text(self.visit_type_group, name).click()
        return self

    @property
    def an_option_select(self):
        return self.start_visit_form.locator('select.cds--select-input[title="Select an option"]')

    def select_an_option(self, option_label: str):
        self.an_option_select.select_option(label=option_label)

    @property
    def punctuality_select(self) -> Locator:
        return self.start_visit_form.get_by_label("Punctuality (optional)")

    def set_punctuality(self, punctuality_type: str):
        self.punctuality_select.select_option(label=punctuality_type)
        return self

    @property
    def start_visit(self):
        return self.start_visit_form.get_by_text("Start visit")

    def click_start_visit(self):
        self.start_visit.click()
        return self

    def should_have_active_visit(self):
        expect(self.active_visit).to_be_visible()
        return self

    def should_not_have_active_visit(self):
        expect(self.active_visit).to_be_hidden()
        return self

    def should_have_punctuality(self, punctuality: str):
        expect(self.chosen_punctuality(punctuality)).to_be_visible()
        return self

    # ------End visit modal ------

    @property
    def end_visit_modal(self) -> Locator:
        return self.page.get_by_role("dialog")

    @property
    def end_visit_modal_title(self) -> Locator:
        return self.end_visit_modal.locator("h2.cds--modal-header__heading")

    @property
    def end_visit_cancel_button(self) -> Locator:
        return self.end_visit_modal.get_by_role("button", name=re.compile(r"Cancel", re.I))

    @property
    def end_visit_confirm_button(self) -> Locator:
        return self.end_visit_modal.get_by_role("button", name=re.compile(r"End Visit", re.I))

    def should_see_end_visit_modal(self):
        expect(self.end_visit_modal).to_be_visible()
        expect(self.end_visit_modal_title).to_contain_text("end this active visit")
        return self

    def confirm_end_visit(self):
        expect(self.end_visit_modal).to_be_visible()
        self.end_visit_confirm_button.click()
        expect(self.end_visit_modal).to_be_hidden()
        return self

    # ---------- Helpers ----------

    def get_patient_uuid(self) -> str:
        return self.page.url.split("/patient/")[1].split("/")[0]

    def should_be_opened(self):
        url = self.page.url
        assert "/patient/" in url

        return self

    def get_patient_name_locator(self, name: str) -> Locator:
        return self.patient_banner.get_by_text(name)
