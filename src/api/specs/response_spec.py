from collections.abc import Callable
from http import HTTPStatus
from json import JSONDecodeError

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
        def check(response: Response):
            assert response.status_code == HTTPStatus.BAD_REQUEST, response.text

            try:
                error_content = response.json().get("error").get("message")
            except JSONDecodeError:
                error_content = response.content
            error_text = str(error_content)

            assert error_msg in error_text, (
                f"Expected error message '{error_msg}',\nbut got '{error_text}'."
            )

        return check

    @staticmethod
    def request_returns_unauthorized_with_message(error_msg: str) -> Callable:
        def check(response: Response):
            assert response.status_code == HTTPStatus.UNAUTHORIZED, response.text

            try:
                error_content = response.json().get("error").get("message")
            except JSONDecodeError:
                error_content = response.content
            error_text = str(error_content)

            assert error_msg in error_text, (
                f"Expected error message '{error_msg}',\nbut got '{error_text}'."
            )

        return check

    @staticmethod
    def request_returns_forbidden_with_message(error_msg: str) -> Callable:
        def check(response: Response):
            assert response.status_code == HTTPStatus.FORBIDDEN, response.text

            try:
                error_content = response.json().get("error").get("message")
            except JSONDecodeError:
                error_content = response.content
            error_text = str(error_content)

            assert error_msg in error_text, (
                f"Expected error message '{error_msg}',\nbut got '{error_text}'."
            )

        return check