from collections.abc import Callable
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any

from requests import Response


class ResponseSpecs:

    @staticmethod
    def request_returns_ok() -> Callable:
        def check(response: Response):
            assert response.status_code == HTTPStatus.OK, response.text
        return check

    @staticmethod
    def entity_was_created() -> Callable:
        def check(response: Response):
            assert response.status_code == HTTPStatus.CREATED, response.text
        return check

    @staticmethod
    def entity_was_deleted() -> Callable:
        def check(response: Response):
            assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.OK, HTTPStatus.NO_CONTENT), response.text
        return check

    @staticmethod
    def entity_not_found(error_msg: str) -> Callable:
        return lambda res: ResponseSpecs._base_error_check(
            res, HTTPStatus.NOT_FOUND, ResponseSpecs._standard_error_extractor, error_msg
        )

    @staticmethod
    def request_returns_bad_request(error_key: str, error_value: str) -> Callable:
        def check(response: Response):
            assert response.status_code == HTTPStatus.BAD_REQUEST, response.text

            try:
                error_content = response.json().get(error_key)
            except JSONDecodeError:
                error_content = response.content
            error_text = str(error_content)

            assert error_value in error_text, (
                    f"\nExpected {error_text}\n, "
                    f"Got {error_content}")

        return check

    @staticmethod
    def request_returns_bad_request_with_message(error_msg: str) -> Callable:
        return lambda res: ResponseSpecs._base_error_check(
            res, HTTPStatus.BAD_REQUEST, ResponseSpecs._standard_error_extractor, error_msg
        )

    @staticmethod
    def request_returns_error() -> Callable:
        def check(response: Response):
            assert response.status_code >= 400, response.text
        return check

    @staticmethod
    def request_returns_unauthorized_with_message(error_msg: str) -> Callable:
        return lambda res: ResponseSpecs._base_error_check(
            res, HTTPStatus.UNAUTHORIZED, ResponseSpecs._standard_error_extractor, error_msg
        )

    @staticmethod
    def request_returns_forbidden_with_message(error_msg: str) -> Callable:
        return lambda res: ResponseSpecs._base_error_check(
            res, HTTPStatus.FORBIDDEN, ResponseSpecs._standard_error_extractor, error_msg
        )

    @staticmethod
    def _base_error_check(response: Response, status_code: HTTPStatus, extract_fn: Callable[[dict], Any],
                          expected_msg: str):
        """Базовый метод для проверки статус-кода и наличия сообщения в JSON."""
        assert response.status_code == status_code, response.text

        try:
            data = response.json()
            error_content = extract_fn(data)
        except (JSONDecodeError, AttributeError, TypeError):
            error_content = response.content

        error_text = str(error_content)
        assert expected_msg in error_text, (
            f"Expected error message '{expected_msg}',\nbut got '{error_text}'."
        )

    @staticmethod
    def _standard_error_extractor(data: dict) -> Any:
        """Стандартный путь для большинства ошибок: error -> message"""
        return data.get("error", {}).get("message")

    def request_returns_not_found_with_message(error_msg: str) -> Callable:
        def check(response: Response):
            assert response.status_code == HTTPStatus.NOT_FOUND, response.text
            try:
                msg = response.json().get("error", {}).get("message")
            except JSONDecodeError:
                msg = response.text
            assert error_msg in str(msg), response.text
        return check

    @staticmethod
    def request_returns_ok_or_not_found():
        def check(response: Response):
            assert response.status_code in (HTTPStatus.OK, HTTPStatus.NOT_FOUND), response.text
        return check
