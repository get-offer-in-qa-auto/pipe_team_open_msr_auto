from typing import TypeVar, Dict, Callable, Optional, Any

from src.api.models.base_model import BaseModel
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.requests.sceleton.http_request import HTTPRequest
from src.api.requests.sceleton.requesters.crud_requester import CrudRequester

T = TypeVar('T', bound=BaseModel)


class ValidatedCrudRequester(HTTPRequest):
    def __init__(self, request_spec: Dict[str, str], endpoint: Endpoint, response_spec: Callable):
        super().__init__(request_spec, endpoint, response_spec)
        self.crud_requester = CrudRequester(request_spec = request_spec, endpoint = endpoint, response_spec = response_spec)

    def post(self, model: Optional[T] = None):
        response = self.crud_requester.post(model= model)
        return self.endpoint.value.response_model.model_validate(response.json())

    def get(self, id: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        response = self.crud_requester.get(id=id, params=params)
        return self.endpoint.value.response_model.model_validate(response.json())

    def update(self,  model: T):
        response = self.crud_requester.update(model=model)
        return self.endpoint.value.response_model.model_validate(response.json())

