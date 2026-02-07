
import pytest

from src.api.classes.api_manager import ApiManager
from src.api.models.comparison.entity_assertions import EntityAssertions
from src.api.models.requests.create_visit_request import CreateVisitRequest


@pytest.mark.api
def test_create_visit(api_manager: ApiManager, create_visit_request: CreateVisitRequest):
    created_visit = api_manager.visit_steps.create_visit(create_visit_request)
    EntityAssertions.has_uuid(created_visit)
