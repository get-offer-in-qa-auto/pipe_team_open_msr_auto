from playwright.sync_api import expect

from src.ui.base_page import BasePage


class OpenMsrHomePage(BasePage):

    @property
    def add_patient_button(self):
        return self.page.locator('button[name="AddPatientIcon"]')

    #TODO:
    def url(self) -> str:
        return "/home/service-queues"

    def click_add_patient(self):
        self.add_patient_button.click()
        return self


    def wait_until_loaded(self):
        expect(
            self.page.get_by_role("button", name="Add Patient")
        ).to_be_visible(timeout=15_000)
        return self


