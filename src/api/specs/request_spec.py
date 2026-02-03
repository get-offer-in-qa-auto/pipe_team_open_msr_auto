import base64



class RequestSpecs:

    @staticmethod
    def default_request_headers():
        return {
            'Content-Type': 'application/json',
        }

    @staticmethod
    def admin_auth_spec():
        raw = "admin:Admin123"
        token = base64.b64encode(raw.encode()).decode()
        headers = RequestSpecs.default_request_headers()
        headers["authorization"] = f"Basic {token}"
        return headers



