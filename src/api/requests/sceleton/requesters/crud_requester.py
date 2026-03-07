from typing import Any, Dict, Optional, TypeVar

import requests
from requests import Response

from src.api.configs.config import Config
from src.api.coverage.api_coverage_collector import ApiCoverageCollector
from src.api.models.base_model import BaseModel
from src.api.requests.sceleton.http_request import HTTPRequest
from src.api.requests.sceleton.interfaces.crud_end_interface import CrudEndPointInterface

# дженерик, позволяющий сохранять строгую типизацию
T = TypeVar('T', bound=BaseModel)


class CrudRequester(HTTPRequest, CrudEndPointInterface):
    def _record_coverage(self, method: str, path: str) -> None:
        ApiCoverageCollector.record(method=method, path=path)

    # TODO мы же наследовались тут почему возвращаемы тип другой - не бейс модел
    def post(self, model: Optional[T]) -> Response:
        # TODO: optimize
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        body = model.model_dump() if model else ''
        self._record_coverage("POST", self.endpoint.value.url)

        response = requests.post(
            url=f'{server_url}{api_version_url}{self.endpoint.value.url}', headers=self.request_spec, json=body
        )
        self.response_spec(response)
        return response

    def get(
        self,
        model: Optional[BaseModel] = None,
        id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        url = f'{server_url}{api_version_url}{self.endpoint.value.url}'
        path = self.endpoint.value.url

        if id:
            url = f"{url}/{id}"
            path = f"{self.endpoint.value.url}/{{uuid}}"

        self._record_coverage("GET", path)

        response = requests.get(url=url, headers=self.request_spec, params=params)
        self.response_spec(response)
        return response

    def update(self, model: Optional[BaseModel] = None) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        url = f'{server_url}{api_version_url}{self.endpoint.value.url}'
        body = model.model_dump() if model else {}

        self._record_coverage("PUT", self.endpoint.value.url)

        response = requests.put(url=url, headers=self.request_spec, json=body)

        self.response_spec(response)
        return response

    def update_by_post(self, id: str, model: Optional[T] = None) -> Response:
        server_url = Config.get("server")
        api_version_url = Config.get("api_version")

        body = model.model_dump(exclude_none=True) if model else {}
        url = f"{server_url}{api_version_url}{self.endpoint.value.url}/{id}"

        self._record_coverage("POST", f"{self.endpoint.value.url}/{{uuid}}")

        response = requests.post(
            url=url,
            headers=self.request_spec,
            json=body,
        )
        self.response_spec(response)
        return response

    def delete(self, id: int) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        self._record_coverage("DELETE", f"{self.endpoint.value.url}/{{uuid}}")

        response = requests.delete(
            url=f'{server_url}{api_version_url}{self.endpoint.value.url}/{id}', headers=self.request_spec
        )
        self.response_spec(response)
        return response

    def delete_with_params(
        self,
        id: str,
        params: Optional[Dict[str, Any]] = None,
        url_metadata: Optional[Dict[str, Any]] = None
    ) -> Response:
        server_url = Config.get('server')
        api_version_url = Config.get('api_version')

        template_url = self.endpoint.value.url
        request_url = template_url

        if url_metadata:
            for key, value in url_metadata.items():
                request_url = request_url.replace(f":{key}", str(value))

        coverage_parts = []
        for part in template_url.split("/"):
            if not part:
                continue
            if part.startswith(":"):
                coverage_parts.append("{uuid}")
            else:
                coverage_parts.append(part)

        normalized_template_url = "/" + "/".join(coverage_parts)
        normalized_path = f"{normalized_template_url}/{{uuid}}"
        self._record_coverage("DELETE", normalized_path)

        url = f'{server_url}{api_version_url}{request_url}/{id}'
        response = requests.delete(url=url, headers=self.request_spec, params=params)
        self.response_spec(response)
        return response
