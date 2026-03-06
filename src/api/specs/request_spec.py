import base64
from typing import Dict

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
