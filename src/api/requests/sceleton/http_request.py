from collections.abc import Callable
from typing import Protocol, Dict

from src.api.requests.sceleton.endpoint import Endpoint


class HTTPRequest(Protocol):
    def __init__(self, request_spec: Dict[str,str], endpoint: Endpoint, response_spec: Callable):
        self.request_spec = request_spec
        self.endpoint = endpoint
        self.response_spec = response_spec