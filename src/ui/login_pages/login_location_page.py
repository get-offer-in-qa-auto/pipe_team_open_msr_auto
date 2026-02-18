import random

from playwright.sync_api import expect

from src.ui.base_page import BasePage


class LoginLocationPage(BasePage):

    @property
    def welcome_text(self):
        return self.page.get_by_text("Welcome")

    @property
    def username_input(self):
        return self.page.locator("#username")

    @property
    def list_of_location_elements(self):
        return self.page.locator('input[type="radio"]')

    def select_random_location(self):
        radios = self.list_of_location_elements

        # ждём, пока радиокнопки реально появятся
        expect(radios.first).to_be_visible(timeout=10_000)

        count = radios.count()
        if count == 0:
            raise AssertionError("Location radio buttons not found")

        idx = random.randrange(count)
        radio = radios.nth(idx)

        # скроллим к элементу (часто спасает)
        radio.scroll_into_view_if_needed()

        # иногда check() не кликает, если input перекрыт/скрыт
        try:
            radio.check(timeout=10_000)
        except Exception:
            # fallback: кликаем с force (только для дебага/нестабильной верстки)
            radio.click(force=True, timeout=10_000)

        # финальная проверка
        expect(radio).to_be_checked()

    @property
    def confirm_button(self):
        return self.page.get_by_role("button", name="Confirm")


    def url(self) -> str:
        return "/login/location"

    def select_location(self):
        self.select_random_location()
        self.confirm_button.click()
        return self
