import pytest
from playwright.sync_api import Page

from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.ui.initial_setup_page import InitialSetupPage
from src.ui.login_pages.login_page import LoginPage


class TestAppSetup:
    @pytest.mark.browsers('chrome')
    @pytest.mark.usefixtures("admin_user_request")
    @pytest.mark.app_setup
    def test_app_setup(self, page: Page, admin_user_request: BaseCreateUserRequest):
        InitialSetupPage(page).open() \
            .wait_for_setup_to_be_finished()\
            .get_page(LoginPage).open() \
            .login_as_success(admin_user_request) \
            .should_see_welcome()
