from src.ui.base_page import BasePage


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

    def url(self) -> str:
        return "/login"

    def login(self, username: str, password: str):
        self.username_input.fill(username)
        self.continue_button.click()
        self.password_input.fill(password)
        self.login_button.click()
        return self

