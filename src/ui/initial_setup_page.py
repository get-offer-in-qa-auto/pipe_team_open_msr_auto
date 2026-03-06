from playwright.sync_api import expect

from src.api.configs.config import Config
from src.ui.base_page import BasePage


class InitialSetupPage(BasePage):
    def open(self) -> "InitialSetupPage":
        base_url = str(Config.get('UI_BASE_URL', 'http://localhost:3000')).strip('/')
        target = f'{base_url}{self.url()}'
        self.page.goto(target, wait_until="domcontentloaded")
        return self

    def url(self) -> str:
        return "/initialsetup#"

    def wait_for_setup_to_be_finished(self):
        def is_finished(response):
            if "openmrs/initialsetup" in response.url and response.status == 200:
                try:
                    return response.json().get("initializationComplete") is True
                except:
                    return False
            return False

        self.page.wait_for_event("response", is_finished, timeout=3_600_000)
        return self