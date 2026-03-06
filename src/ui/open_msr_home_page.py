import allure
from playwright.sync_api import expect

from src.ui.base_page import BasePage
from src.ui.components.header_search_component import HeaderSearchComponent


class OpenMsrHomePage(BasePage):

    @property
    @allure.step("add_patient_button")
    def add_patient_button(self):
        return self.page.locator('button[name="AddPatientIcon"]')

    @property
    @allure.step("header_search")
    def header_search(self):
        return HeaderSearchComponent(self.page)
    #TODO:
    @allure.step("url")
    def url(self) -> str:
        return "/home/service-queues"

    @allure.step("click_add_patient")
    def click_add_patient(self):
        self.add_patient_button.click()
        return self


    @allure.step("wait_until_loaded")
    def wait_until_loaded(self):
        expect(
            self.page.get_by_role("button", name="Add Patient")
        ).to_be_visible(timeout=15_000)
        return self

    @allure.step("should_have_add_patient_button")
    def should_have_add_patient_button(self):
        expect(self.add_patient_button).to_be_visible()
        return self


