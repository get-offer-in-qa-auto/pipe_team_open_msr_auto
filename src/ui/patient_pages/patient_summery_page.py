from playwright.sync_api import Locator

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

    # ---------- Helpers ----------

    def get_patient_uuid(self) -> str:
        return self.page.url.split("/patient/")[1].split("/")[0]

    def should_be_opened(self):
        url = self.page.url
        assert "/patient/" in url
        #assert "Summary" in url???

        return self

    def get_patient_name_locator(self, name: str) -> Locator:
        return self.patient_banner.get_by_text(name)
