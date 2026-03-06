import allure
from playwright.sync_api import expect

from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.ui.base_page import BasePage
from src.ui.login_pages.login_location_page import LoginLocationPage


class LoginPage(BasePage):
    @property
    def username_input(self):
        return self.page.locator("#username")

    @property
    def continue_button(self):
        return self.page.get_by_role("button", name="Continue")

    @property
    def password_input(self):
        return self.page.locator("#password")

    @property
    def login_button(self):
        return self.page.get_by_role("button", name="Log in")

    @property
    def notification_error(self):
        return self.page.locator(".cds--inline-notification--error[role='status']")

    def url(self) -> str:
        return "/login"

    @allure.step("should_have_error_message")
    def should_have_error_message(self, message: str):
        expect(self.notification_error).to_be_visible()
        expect(self.notification_error).to_contain_text(message)
        return self

    @allure.step("login")
    def login(self, username: str, password: str) -> "LoginPage":
        self.username_input.fill(username)
        self.continue_button.click()
        self.password_input.fill(password)
        self.login_button.click()
        return self

    @allure.step("login_success")
    def login_success(self, username: str, password: str) -> LoginLocationPage:
        self.login(username, password)
        return LoginLocationPage(self.page)

    @allure.step("login_as")
    def login_as(self, user: BaseCreateUserRequest) -> "LoginPage":
        return self.login(user.username, user.password)

    @allure.step("login_as_success")
    def login_as_success(self, user: BaseCreateUserRequest) -> LoginLocationPage:
        return self.login_success(user.username, user.password)
