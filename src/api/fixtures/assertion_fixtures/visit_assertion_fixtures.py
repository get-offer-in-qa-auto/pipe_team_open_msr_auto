import pytest

from src.api.models.comparison.model_assertions import ModelAssertions
from src.api.models.responses.create_visit_response import CreateVisitResponse


@pytest.fixture(autouse=True)
def check_visit_persisted(request):
    mark = request.node.get_closest_marker("check_visit_persisted")
    if not mark:
        yield
        return

    api_manager = request.getfixturevalue("api_manager")
    created_objects = request.getfixturevalue("created_objects")
    create_visit_request = request.getfixturevalue("create_visit_request")

    yield

    created_visits = [o for o in created_objects if isinstance(o, CreateVisitResponse)]
    assert len(created_visits) == 1, (
        f"Check_visit_persisted expects exactly 1 created visit, got {len(created_visits)}."
    )

    created_visit = created_visits[0]
    visit_full = api_manager.visit_steps.get_visit_by_uuid(created_visit.uuid)

    ModelAssertions(create_visit_request, visit_full).match()


@pytest.fixture(autouse=True)
def check_visit_not_created(request):
    mark = request.node.get_closest_marker("check_visit_not_created")
    if not mark:
        yield
        return

    created_objects = request.getfixturevalue("created_objects")

    yield

    created_visits = [o for o in created_objects if isinstance(o, CreateVisitResponse)]
    assert len(created_visits) == 0, (
        f"Expected no visit to be created, but found {len(created_visits)} CreateVisitResponse in created_objects."
    )