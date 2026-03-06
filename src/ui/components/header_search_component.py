import allure
from playwright.sync_api import expect


class HeaderSearchComponent:

    @allure.step("__init__")
    def __init__(self, page):
        self.page = page

    @property
    @allure.step("search_icon")
    def search_icon(self):
        return self.page.get_by_test_id("searchPatientIcon")

    @property
    @allure.step("search_input")
    def search_input(self):
        return self.page.get_by_placeholder(
            "Search for a patient by name or identifier number"
        )

    @property
    @allure.step("results_container")
    def results_container(self):
        return self.page.get_by_test_id("floatingSearchResultsContainer")

    # ---------- Actions ----------

    @allure.step("open_search")
    def open_search(self):
        self.search_icon.click()
        expect(self.search_input).to_be_visible()
        return self

    @allure.step("search")
    def search(self, text: str):
        self.search_input.fill(text)
        return self

    @allure.step("select_first_result")
    def select_first_result(self):
        link = self.results_container.locator("a").first
        expect(link).to_be_visible()
        link.click()
        return self

    @allure.step("should_have_result")
    def should_have_result(self, text: str):
        expect(self.page.get_by_text(text)).to_be_visible()
        return self

    @allure.step("should_have_no_results")
    def should_have_no_results(self):
        # ждём пока dropdown отрисуется
        expect(self.results_container).to_be_visible()

        # убеждаемся, что ссылок с пациентами нет
        expect(
            self.results_container.locator("a")
        ).to_have_count(0)

        return self