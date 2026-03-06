from __future__ import annotations

import allure
from requests import Response

from src.api.models.comparison.entity_assertions import EntityAssertions
from src.api.models.requests.create_visit_request import CreateVisitInvalidRequest, CreateVisitRequest
from src.api.models.requests.update_visit_request import UpdateVisitRequest
from src.api.models.responses.create_visit_response import CreateVisitResponse
from src.api.models.responses.get_visit_response import VisitFullResponse
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.specs.response_spec import ResponseSpecs
from src.api.steps.base_steps import BaseSteps


class VisitSteps(BaseSteps):
    @allure.step("get_visit_by_uuid")
    def get_visit_by_uuid(self, visit_uuid: str) -> VisitFullResponse:
        """GET /visit/{uuid} in FULL representation (v=full)."""
        return self._vcr(
            endpoint=Endpoint.GET_VISIT,
            response_spec=ResponseSpecs.request_returns_ok(),
        ).get(id=visit_uuid, params={"v": "full"})

    @allure.step("get_visit_raw_by_uuid")
    def get_visit_raw_by_uuid(self, visit_uuid: str, response_spec) -> Response:
        """GET /visit/{uuid} and return raw Response (no pydantic validation)."""
        return self._cr(
            endpoint=Endpoint.GET_VISIT,
            response_spec=response_spec,
        ).get(id=visit_uuid, params={"v": "full"})

    @allure.step("create_visit")
    def create_visit(self, create_visit_request: CreateVisitRequest) -> CreateVisitResponse:
        created: CreateVisitResponse = self._vcr(
            endpoint=Endpoint.CREATE_VISIT,
            response_spec=ResponseSpecs.entity_was_created(),
        ).post(create_visit_request)

        EntityAssertions.has_uuid(created)

        self.created_objects.append(created)
        return created

    @allure.step("create_raw_visit")
    def create_raw_visit(
        self, payload: CreateVisitInvalidRequest, error_key: str | None = None, error_value: str | None = None
    ):
        return self._cr(
            endpoint=Endpoint.CREATE_VISIT,
            response_spec=ResponseSpecs.request_returns_bad_request(error_key, error_value),
        ).post(payload)

    @allure.step("delete_visit")
    def delete_visit(self, visit_uuid: str, purge: bool = True) -> None:
        """Delete/purge visit (DELETE /visit/{uuid}?purge=true)."""
        params = {"purge": "true"} if purge else None

        self._cr(
            endpoint=Endpoint.DELETE_VISIT,
            response_spec=ResponseSpecs.entity_was_deleted(),
        ).delete_with_params(id=visit_uuid, params=params)

    @allure.step("update_visit")
    def update_visit(self, visit_uuid: str, update_visit_request: CreateVisitRequest) -> CreateVisitResponse:
        updated: CreateVisitResponse = self._vcr(
            endpoint=Endpoint.UPDATE_VISIT,
            response_spec=ResponseSpecs.request_returns_ok(),
        ).update_by_post(update_visit_request, visit_uuid)

        EntityAssertions.has_uuid(updated)
        return updated

    @allure.step("update_invalid_visit")
    def update_invalid_visit(self, visit_uuid: str, payload: UpdateVisitRequest, error_key: str, error_value: str):
        return self._cr(
            endpoint=Endpoint.UPDATE_VISIT,
            response_spec=ResponseSpecs.request_returns_bad_request(error_key, error_value),
        ).update_by_post(model=payload, id=visit_uuid),
