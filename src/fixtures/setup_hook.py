from typing import List

import pytest
from playwright.sync_api import Page

from src.api.classes.session_storage import SessionStorage
from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.ui.login_pages.login_page import LoginPage
from src.ui.open_msr_home_page import OpenMsrHomePage
from src.utils.browsers import norm_browser_name


@pytest.fixture(autouse=True)
def user_session_extension(
    request: pytest.FixtureRequest,
    page: Page,
    user_factory,
):
    mark = request.node.get_closest_marker("user_session")
    if not mark:
        yield
        return

    count = max(1, int(mark.args[0]))
    auth_index = int(mark.kwargs.get("auth", 0))

    users: List[BaseCreateUserRequest] = [
        user_factory() for _ in range(count)
    ]
    SessionStorage.add_users(users)
    LoginPage(page).auth_as_user(page, users[auth_index])

    yield

    SessionStorage.clear()


@pytest.fixture(autouse=True)
def admin_session_autologin(
    request: pytest.FixtureRequest,
    page: Page,
    admin_user_request,
    api_manager
):
    mark = request.node.get_closest_marker("admin_session")
    if not mark:
        yield
        return

    locations = api_manager.user_steps.get_locations()
    target = locations.results[0]  # или выбери по display

    OpenMsrHomePage(page).auth_as_user(
        admin_user_request,
        location_uuid=target.uuid,
        location_display=target.display,
    )


    OpenMsrHomePage(page).open().wait_until_loaded()
    yield



@pytest.fixture(autouse=True)
def browser_match_guard(request):
    mark = request.node.get_closest_marker("browsers")
    if not mark:
        return

    allowed = {
        norm_browser_name(browser_name)
        for browser_name in mark.args
    }
    if not allowed:
        return

    try:
        current = request.getfixturevalue("browser_name")
    except Exception:
        return

    if norm_browser_name(current) not in allowed:
        pytest.skip(
            f"Пропущен: текущий браузер {current} не в {sorted(allowed)}"
        )