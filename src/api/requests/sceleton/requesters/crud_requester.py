from http import HTTPStatus
from typing import Protocol, Optional, Union, TypeVar, Dict, Any

import requests
from requests import Response

from src.api.configs.config import Config
from src.api.models.base_model import BaseModel
from src.api.requests.sceleton.http_request import HTTPRequest
from src.api.requests.sceleton.interfaces.crud_end_interface import CrudEndPointInterface

#дженерик, позволяющий сохранять строгую типизацию
T = TypeVar('T', bound=BaseModel)

class CrudRequester(HTTPRequest, CrudEndPointInterface):
    #TODO мы же наслодовались тут почему возвращаемы тип другой - не бейс модел
    def post(self, model: Optional[T]) -> Response:
        #TODO: optimize
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')


        body = model.model_dump() if model else ''
        response = requests.post(url=f'{server_url}{api_version_url}{self.endpoint.value.url}',
                                 headers=self.request_spec, json=body)
        self.response_spec(response)
        return response



    def get(self, model: Optional[BaseModel] = None, id: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        url = f'{server_url}{api_version_url}{self.endpoint.value.url}'
        if id:
            url = f"{url}/{id}"

        response = requests.get(url=url, headers=self.request_spec, params=params)
        self.response_spec(response)
        return response

    def update(self, model: Optional[BaseModel] = None) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        url = f'{server_url}{api_version_url}{self.endpoint.value.url}'
        body = model.model_dump() if model else {}

        response = requests.put(
            url=url,
            headers=self.request_spec,
            json=body
        )

        self.response_spec(response)
        return response

    #TODO мы же наслодовались тут почему возвращаемы тип другой - не бейс модел
    def delete(self, id: int) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        response = requests.delete(url=f'{server_url}{api_version_url}{self.endpoint.value.url}/{id}',
                                 headers=self.request_spec)
        self.response_spec(response)
        return response

    def delete_with_params(self, id: str, params: Optional[Dict[str, Any]] = None) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        url = f'{server_url}{api_version_url}{self.endpoint.value.url}/{id}'
        response = requests.delete(url=url, headers=self.request_spec, params=params)
        self.response_spec(response)
        return response
