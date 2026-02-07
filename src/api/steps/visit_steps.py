from __future__ import annotations

from src.api.models.comparison.entity_assertions import EntityAssertions
from src.api.models.comparison.model_assertions import ModelAssertions
from src.api.models.requests.create_visit_request import CreateVisitRequest, CreateVisitInvalidRequest
from src.api.models.responses.create_visit_response import VisitCreateResponse
from src.api.models.responses.get_visit_response import VisitFullResponse
from src.api.requests.sceleton.endpoint import Endpoint
from src.api.specs.response_spec import ResponseSpecs
from src.api.steps.base_steps import BaseSteps


class VisitSteps(BaseSteps):
    def get_visit_full(self, visit_uuid: str) -> VisitFullResponse:
        return self._vcr(
            endpoint=Endpoint.GET_VISIT,
            response_spec=ResponseSpecs.request_returns_ok(),
        ).get(id=visit_uuid, params={"v": "full"})

    def create_visit(self, create_visit_request: CreateVisitRequest) -> VisitCreateResponse:
        created: VisitCreateResponse = self._vcr(
            endpoint=Endpoint.CREATE_VISIT,
            response_spec=ResponseSpecs.entity_was_created(),
        ).post(create_visit_request)

        EntityAssertions.has_uuid(created)

        full = self.get_visit_full(created.uuid)
        ModelAssertions(create_visit_request, full).match()

        self.created_objects.append(created)
        return created

    def create_invalid_visit(
        self,
        payload: CreateVisitInvalidRequest,
        error_key: str | None = None,
        error_value: str | None = None,
    ):
        return self._cr(
            endpoint=Endpoint.CREATE_VISIT,
            response_spec=ResponseSpecs.request_returns_bad_request(error_key, error_value),
        ).post(payload)

    def delete_visit(self, visit_uuid: str, purge: bool = True) -> None:
        """Delete/purge visit (DELETE /visit/{uuid}?purge=true)."""
        params = {"purge": "true"} if purge else None

        self._cr(
            endpoint=Endpoint.DELETE_VISIT,
            response_spec=ResponseSpecs.entity_was_deleted(),
        ).delete_with_params(id=visit_uuid, params=params)