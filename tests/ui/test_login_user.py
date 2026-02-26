import pytest
from playwright.sync_api import expect, Page

from src.api.constants.error_messages import ErrorMessages
from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.ui.login_pages.login_location_page import LoginLocationPage
from src.ui.login_pages.login_page import LoginPage
from src.ui.open_msr_home_page import OpenMsrHomePage


@pytest.mark.ui
#TODO: test with some browser
@pytest.mark.browsers("chromium")
class TestLoginUser:

    @pytest.mark.usefixtures("admin_user_request")
    def test_admin_can_login_with_correct_data(
        self,
        page: Page,
        admin_user_request: BaseCreateUserRequest
    ):
        login_location_page = (
            LoginPage(page)
            .open()
            .login(
                admin_user_request.username,
                admin_user_request.password
            )
            .get_page(LoginLocationPage)
        )

        expect(login_location_page.welcome_text).to_be_visible()

        open_msr_home_page = (
            LoginLocationPage(page).select_location()
            .get_page(OpenMsrHomePage))



        expect(open_msr_home_page.add_patient_button).to_be_visible()

    @pytest.mark.usefixtures('api_manager', 'create_user_with_roles')
    def test_login_as_disabled_user(self, api_manager, page, create_user_with_roles):
        user_request, user_data = create_user_with_roles()
        api_manager.user_steps.delete_user(user_data.uuid, purge=False)

        LoginPage(page)\
        .open()\
        .login(
            user_request.username,
            user_request.password
        )\
        .should_have_error_message(ErrorMessages.INVALID_USERNAME_OR_PASSWORD)
