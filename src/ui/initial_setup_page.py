from playwright.sync_api import expect

from src.api.configs.config import Config
from src.ui.base_page import BasePage


class InitialSetupPage(BasePage):
    def open(self) -> "InitialSetupPage":
        base_url = str(Config.get('UI_BASE_URL', 'http://localhost:3000')).strip('/')
        self.page.goto(base_url, wait_until="domcontentloaded")
        return self

    def url(self) -> str:
        return "/initialsetup#"

    def get_row_with_text(self, text: str):
        return self.page.locator('tr').filter(has_text=text)

    def wait_for_progress(self, task_name: str, progress: int):
        if not (1 <= progress <= 100):
            raise AssertionError('progress should be between 1 and 100')

        row_locator = self.get_row_with_text(task_name)
        progress_bar = row_locator.locator(".progressBarContainer[role='progressbar']")
        expect(progress_bar).to_have_attribute("aria-valuenow", f"{progress}", timeout=300_000)

        return self

    def wait_for_setup_to_be_finished(self):
        def is_finished(response):
            if "progress.vm.ajaxRequest" in response.url and response.status == 200:
                try:
                    return response.json().get("initializationComplete") is True
                except:
                    return False
            return False

        self.page.wait_for_event("response", is_finished, timeout=1_800_000)
        return self