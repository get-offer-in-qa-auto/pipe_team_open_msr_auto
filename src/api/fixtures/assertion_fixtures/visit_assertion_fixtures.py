import pytest
from src.api.models.comparison.model_assertions import ModelAssertions
from src.api.models.responses.create_visit_response import CreateVisitResponse
from src.api.specs.response_spec import ResponseSpecs


@pytest.fixture(autouse=True)
def check_visit_persisted(request):
    mark = request.node.get_closest_marker("check_visit_persisted")
    if not mark:
        yield
        return

    expected_count = int(mark.kwargs.get("expected_count", 1))

    request_source = mark.kwargs.get("request_source", "create_visit_request")

    api_manager = request.getfixturevalue("api_manager")
    created_objects = request.getfixturevalue("created_objects")

    if isinstance(request_source, (list, tuple)):
        create_requests = [request.getfixturevalue(name) for name in request_source]
    else:
        create_requests = [request.getfixturevalue(str(request_source))]

    yield

    created_visits = [o for o in created_objects if isinstance(o, CreateVisitResponse)]
    assert len(created_visits) == expected_count, (
        f"check_visit_persisted expects {expected_count} created visit(s), got {len(created_visits)}."
    )

    assert len(create_requests) == expected_count, (
        f"check_visit_persisted expects {expected_count} request model(s) "
        f"via request_source, got {len(create_requests)}."
    )

    for created_visit, req_model in zip(created_visits, create_requests):
        visit_full = api_manager.visit_steps.get_visit_by_uuid(created_visit.uuid)
        ModelAssertions(req_model, visit_full).match()


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


@pytest.fixture(autouse=True)
def check_visit_deleted(request):
    mark = request.node.get_closest_marker("check_visit_deleted")
    if not mark:
        yield
        return

    api_manager = request.getfixturevalue("api_manager")
    created_objects = request.getfixturevalue("created_objects")

    yield

    created_visits = [o for o in created_objects if isinstance(o, CreateVisitResponse)]
    assert len(created_visits) == 1, f"Expected exactly 1 created visit, got {len(created_visits)}."
    visit_uuid = created_visits[0].uuid
    assert visit_uuid, f"visit_uuid is falsy: {created_visits[0]}"

    api_manager.visit_steps.get_visit_raw_by_uuid(
        visit_uuid,
        response_spec=ResponseSpecs.request_returns_not_found_with_message("doesn't exist"),
    )


@pytest.fixture(autouse=True)
def check_visit_updated(request):
    mark = request.node.get_closest_marker("check_visit_updated")
    if not mark:
        yield
        return

    api_manager = request.getfixturevalue("api_manager")
    created_objects = request.getfixturevalue("created_objects")
    update_visit_request = request.getfixturevalue("update_visit_request")

    yield

    created_visits = [o for o in created_objects if isinstance(o, CreateVisitResponse)]
    assert len(created_visits) == 1, (
        f"check_visit_updated expects exactly 1 created visit, got {len(created_visits)}."
    )

    visit_uuid = created_visits[0].uuid
    visit_full = api_manager.visit_steps.get_visit_by_uuid(visit_uuid)

    assert visit_full.stopDatetime, "stopDatetime is empty after update"
    assert update_visit_request.stopDatetime, "update_visit_request.stopDatetime is empty"
    assert visit_full.stopDatetime[:19] == update_visit_request.stopDatetime[:19], (
        f"stopDatetime mismatch.\n"
        f"Expected (sec): {update_visit_request.stopDatetime[:19]}\n"
        f"Got (sec):      {visit_full.stopDatetime[:19]}\n"
        f"Full got:       {visit_full.stopDatetime}"
    )