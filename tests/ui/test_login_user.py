import allure
import pytest
from playwright.sync_api import Page

from src.api.constants.error_messages import ErrorMessages
from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.ui.login_pages.login_page import LoginPage


@pytest.mark.ui
@pytest.mark.browsers("chromium")
class TestLoginUser:

    #test with some browser
    @allure.title("Admin Can Login With Correct Data")
    @pytest.mark.browsers("chromium")
    @pytest.mark.usefixtures("admin_user_request")
    def test_admin_can_login_with_correct_data(self, page: Page, admin_user_request: BaseCreateUserRequest):
        LoginPage(page) \
            .open() \
            .login_as_success(admin_user_request) \
            .should_see_welcome() \
            .select_location() \
            .should_have_add_patient_button()

    @allure.title("Login As Disabled User")
    @pytest.mark.usefixtures('api_manager', 'create_user_with_roles')
    def test_login_as_disabled_user(self, api_manager, page, create_user_with_roles):
        user_request, user_data = create_user_with_roles()
        api_manager.user_steps.delete_user(user_data.uuid, purge=False)

        LoginPage(page) \
            .open() \
            .login(user_request.username, user_request.password) \
            .should_have_error_message(ErrorMessages.INVALID_USERNAME_OR_PASSWORD)
