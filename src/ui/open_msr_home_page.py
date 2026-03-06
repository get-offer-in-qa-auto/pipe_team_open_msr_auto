from playwright.sync_api import expect

from src.ui.base_page import BasePage
from src.ui.components.header_search_component import HeaderSearchComponent


class OpenMsrHomePage(BasePage):

    @property
    def add_patient_button(self):
        return self.page.locator('button[aria-label="Add patient"]')

    @property
    def header_search(self):
        return HeaderSearchComponent(self.page)
    #TODO:
    def url(self) -> str:
        return "/home/service-queues"

    def click_add_patient(self):
        self.add_patient_button.click()
        return self

    def wait_until_loaded(self):
        expect(self.add_patient_button).to_be_visible(timeout=15_000)
        return self

    def should_have_add_patient_button(self):
        expect(self.add_patient_button).to_be_visible()
        return self


