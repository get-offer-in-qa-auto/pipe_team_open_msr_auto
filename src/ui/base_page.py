import allure
import json
from abc import ABC, abstractmethod
from typing import TypeVar, Type, Callable, List

from playwright.sync_api import Page, Dialog, Locator

from src.api.configs.config import Config
from src.api.models.requests.base_create_user_request import BaseCreateUserRequest
from src.api.specs.request_spec import RequestSpecs
from src.ui.api_flow import ApiFlow

T = TypeVar("T", bound="BasePage")

class BasePage(ABC):
    def __init__(self, page :Page):
        self.page = page
        self.base_url = str(Config.get('UI_BASE_URL','http://localhost:3000')).strip('/')

    def _generate_page_elements(
            self,
            element: Locator,
            constructor: Callable
    ) -> List:
        element.first.wait_for(state="attached", timeout=10_000)
        return [
            constructor(element.nth(index))
            for index in range(element.count())
        ]

    @allure.step("auth_as_user")
    def auth_as_user(
            self,
            user_request: BaseCreateUserRequest,
            *,
            location_uuid: str | None = None,
            location_display: str | None = None,
    ):
        page = self.page
        ui_base = str(Config.get("UI_BASE_URL")).rstrip("/")

        server = str(Config.get("server")).rstrip("/")
        api_ver = str(Config.get("api_version")).strip("/")  # v1
        api_base = f"{server}/{api_ver}"

        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(ui_base + "/login", wait_until="domcontentloaded")

        auth = RequestSpecs.auth_as_user(user_request.username, user_request.password)["Authorization"]

        r1 = page.request.get(
            f"{api_base}/session",
            headers={"Authorization": auth},
        )
        assert r1.ok, f"GET /session failed: {r1.status} {r1.text()}"

        cookies = page.context.cookies()
        assert any(c["name"] == "JSESSIONID" for c in cookies), \
            f"JSESSIONID not found in browser context cookies: {[c['name'] for c in cookies]}"

        if not location_uuid or not location_display:
            rloc = page.request.get(
                f"{api_base}/location",
                headers={"Authorization": auth},
                params={"v": "default", "limit": "50"},
            )
            assert rloc.ok, f"GET /location failed: {rloc.status} {rloc.text()}"
            data = rloc.json()
            results = data.get("results") or []
            assert results, f"No locations returned from /location. Body: {data}"

            target = results[0]
            location_uuid = target["uuid"]
            location_display = target.get("display") or "Unknown"

        payload = {"sessionLocation": location_uuid}

        r2 = page.request.post(
            f"{api_base}/session",
            headers={
                "Authorization": auth,
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),  # data= (строкой), не json=
        )
        assert r2.ok, f"POST /session (set sessionLocation) failed: {r2.status} {r2.text()}"

        page.add_init_script(f"""
            (() => {{
                const loc = {{ uuid: "{location_uuid}", display: "{location_display}" }};
                localStorage.setItem("openmrs:sessionLocation", JSON.stringify(loc));
                localStorage.setItem("queueLocationUuid", loc.uuid);
                localStorage.setItem("queueLocationName", loc.display);
                localStorage.setItem("queueServiceDisplay", "All");
            }})();
        """)

        # 5) сразу открываем home
        page.goto(ui_base + "/home/service-queues", wait_until="domcontentloaded")
        page.reload(wait_until="domcontentloaded")
        return self

    @abstractmethod
    def url(self) -> str:
        raise NotImplementedError

    @allure.step("open")
    def open(self: T) -> T:
        taget = self.url()
        if self.base_url and taget.startswith('/'):
            taget = f'{self.base_url}{taget}'
        self.page.goto(taget, wait_until="domcontentloaded")
        return self

    def get_page(self, page_cls: Type[T]) -> T:
        return page_cls(self.page)

    def check_alert_message_and_accept(self, expected_text: str):
        def _handler(d: Dialog):
            assert expected_text in d.message, f"Alert text mismatch {d.message} "
            d.accept()
        self.page.once("dialog", _handler)
        return self

    @allure.step("switch_to_api")
    def switch_to_api(self, api_manager):
        """
        Generic UI → API switch.
        Specific data (uuid etc.) should be provided by concrete pages.
        """
        return ApiFlow(api_manager=api_manager)
