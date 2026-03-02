from playwright.sync_api import expect


class HeaderSearchComponent:

    def __init__(self, page):
        self.page = page

    @property
    def search_icon(self):
        return self.page.get_by_test_id("searchPatientIcon")

    @property
    def search_input(self):
        return self.page.get_by_placeholder(
            "Search for a patient by name or identifier number"
        )

    @property
    def results_container(self):
        return self.page.get_by_test_id("floatingSearchResultsContainer")

    # ---------- Actions ----------

    def open_search(self):
        self.search_icon.click()
        expect(self.search_input).to_be_visible()
        return self

    def search(self, text: str):
        self.search_input.fill(text)
        return self

    def select_first_result(self):
        link = self.results_container.locator("a").first
        expect(link).to_be_visible()
        link.click()
        return self

    def should_have_result(self, text: str):
        expect(self.page.get_by_text(text)).to_be_visible()
        return self

    def should_have_no_results(self):
        # ждём пока dropdown отрисуется
        expect(self.results_container).to_be_visible()

        # убеждаемся, что ссылок с пациентами нет
        expect(
            self.results_container.locator("a")
        ).to_have_count(0)

        return self