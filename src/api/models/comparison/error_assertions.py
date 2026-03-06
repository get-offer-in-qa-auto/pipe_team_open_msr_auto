class ErrorAssertions:
    @staticmethod
    def status_is(resp, expected: int) -> None:
        assert resp.status_code == expected, (
            f"Expected {expected}, got {resp.status_code}. Body: {getattr(resp, 'text', resp)}"
        )

    @staticmethod
    def has_error(resp) -> dict:
        data = resp.json()
        assert isinstance(data, dict), f"Expected dict JSON, got: {data}"
        assert any(k in data for k in ("error", "errors", "message")), f"No error fields in: {data}"
        return data
