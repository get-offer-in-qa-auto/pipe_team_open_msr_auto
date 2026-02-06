import base64
import logging
from typing import Dict

import requests

from src.api.requests.sceleton.endpoint import Endpoint
from src.api.requests.sceleton.requesters.crud_requester import CrudRequester
from src.api.specs.response_spec import ResponseSpecs


class RequestSpecs:
    @staticmethod
    def default_request_headers() -> Dict[str, str]:
        return {
            'Content-Type': 'application/json',
        }

    @staticmethod
    def unauth_spec() -> Dict[str, str]:
        return RequestSpecs.default_request_headers()

    @staticmethod
    def admin_auth_spec() -> Dict[str, str]:
        return RequestSpecs.auth_as_user('admin', 'Admin123')

    @staticmethod
    def auth_as_user(username, password) -> Dict[str, str]:
        raw = f"{username}:{password}"
        token = base64.b64encode(raw.encode()).decode()
        headers = RequestSpecs.default_request_headers()
        headers["Authorization"] = f"Basic {token}"
        return headers

    @staticmethod
    def auth_as_user_using_session(username, password) -> Dict[str, str]:
        try:
            response: requests.Response = CrudRequester(
                RequestSpecs.auth_as_user(username, password),
                Endpoint.GET_SESSION,
                ResponseSpecs.request_returns_ok()
            ).get()
        except:
            logging.error(f"Authentication failed for {username}")
            raise Exception("Failed to authenticate user")
        else:
            if not response.json().get("authenticated"):
                raise Exception(f"Failed to authenticate '{username}' user via get session request. authenticated = false")
            headers = RequestSpecs.default_request_headers()
            headers["Cookie"] = f"JSESSIONID={response.cookies.get('JSESSIONID')}"
            return headers
