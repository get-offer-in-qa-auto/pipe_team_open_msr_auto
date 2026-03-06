from src.ui.base_page import BasePage


class PatientCreatePage(BasePage):

    def url(self) -> str:
        return "/patient-registration"

    # ---------- Basic Info ----------

    @property
    def given_name_input(self):
        return self.page.locator('input[name="givenName"]')

    @property
    def middle_name_input(self):
        return self.page.locator('input[name="middleName"]')

    @property
    def family_name_input(self):
        return self.page.locator('input[name="familyName"]')

    # ---------- Sex (Carbon UI: click label, not input) ----------

    @property
    def male_radio(self):
        return self.page.locator('label[for="gender-option-male"]')

    @property
    def female_radio(self):
        return self.page.locator('label[for="gender-option-female"]')

    @property
    def unknown_radio(self):
        return self.page.locator('label[for="gender-option-unknown"]')

    # ---------- Birth section helpers ----------

    @property
    def birth_section(self):
        return self.page.locator("//h4[text()='Birth']/parent::div")

    @property
    def dob_known_no_tab(self):
        return self.birth_section.locator('button[role="tab"]', has_text="No")

    @property
    def age_input(self):
        return self.birth_section.locator('#yearsEstimated')

    # (Optional) if you ever need DOB known = Yes later
    @property
    def dob_known_yes(self):
        return self.birth_section.locator('label:has-text("Yes")').first

    # ---------- Submit ----------

    @property
    def register_button(self):
        return self.page.get_by_role("button", name="Register patient")

    # ---------- Actions ----------

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

    def submit(self):
        self.register_button.click()
        return self

    def should_be_opened(self):
        url = self.page.url
        assert self.url() in url

        return self