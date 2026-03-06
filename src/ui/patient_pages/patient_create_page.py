import allure
from src.ui.base_page import BasePage


class PatientCreatePage(BasePage):

    @allure.step("url")
    def url(self) -> str:
        return "/patient-registration"

    # ---------- Basic Info ----------

    @property
    @allure.step("given_name_input")
    def given_name_input(self):
        return self.page.locator('input[name="givenName"]')

    @property
    @allure.step("middle_name_input")
    def middle_name_input(self):
        return self.page.locator('input[name="middleName"]')

    @property
    @allure.step("family_name_input")
    def family_name_input(self):
        return self.page.locator('input[name="familyName"]')

    # ---------- Sex (Carbon UI: click label, not input) ----------

    @property
    @allure.step("male_radio")
    def male_radio(self):
        return self.page.locator('label[for="gender-option-male"]')

    @property
    @allure.step("female_radio")
    def female_radio(self):
        return self.page.locator('label[for="gender-option-female"]')

    @property
    @allure.step("unknown_radio")
    def unknown_radio(self):
        return self.page.locator('label[for="gender-option-unknown"]')

    # ---------- Birth section helpers ----------

    @property
    @allure.step("birth_section")
    def birth_section(self):
        # Finds the section that contains the "Birth" heading (stable vs locator(".."))
        return self.page.locator("section").filter(
            has=self.page.get_by_role("heading", name="Birth")
        )

    @property
    @allure.step("dob_known_no_tab")
    def dob_known_no_tab(self):
        return self.birth_section.locator(
            'button[role="tab"][aria-selected="false"]:has(span[title="No"])'
        ).nth(1)

    @property
    @allure.step("age_input")
    def age_input(self):
        return self.birth_section.locator('#yearsEstimated')

    # (Optional) if you ever need DOB known = Yes later
    @property
    @allure.step("dob_known_yes")
    def dob_known_yes(self):
        return self.birth_section.locator('label:has-text("Yes")').first

    # ---------- Submit ----------

    @property
    @allure.step("register_button")
    def register_button(self):
        return self.page.get_by_role("button", name="Register patient")

    # ---------- Actions ----------

    @allure.step("fill_basic_info")
    def fill_basic_info(
        self,
        given: str,
        family: str,
        gender: str,
        age: int,
        middle: str | None = None,
    ):
        self.given_name_input.fill(given)
        if middle is not None:
            self.middle_name_input.fill(middle)
        self.family_name_input.fill(family)

        g = gender.lower()
        if g == "male":
            self.male_radio.click()
        elif g == "female":
            self.female_radio.click()
        elif g in ("unknown", "other"):
            self.unknown_radio.click()

        # Date of Birth Known? -> No (then Age field appears)
        self.dob_known_no_tab.click()

        # Age
        self.age_input.fill(str(age))

        return self

    @allure.step("submit")
    def submit(self):
        self.register_button.click()
        return self

    @allure.step("should_be_opened")
    def should_be_opened(self):
        url = self.page.url
        assert self.url() in url

        return self