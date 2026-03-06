from typing import Any, Optional

import pytest

from src.api.classes.api_manager import ApiManager


def _resolve_source(request: pytest.FixtureRequest, source: str) -> Any:
    """
    Resolve "fixture_or_param.attr1.attr2" into a concrete value.
    Examples:
      - "username" -> request.getfixturevalue("username")
      - "create_user_request.username" -> request.getfixturevalue("create_user_request").username
    """
    parts = [p for p in source.split(".") if p]
    if not parts:
        raise ValueError("source is empty")

    root = parts[0]

    # Parametrized values live in callspec.params (not always accessible via getfixturevalue on teardown).
    callspec = getattr(request.node, "callspec", None)
    if callspec is not None and root in getattr(callspec, "params", {}):
        value = callspec.params[root]
    else:
        # Fixture values
        value = request.getfixturevalue(root)

    for attr in parts[1:]:
        value = getattr(value, attr)
    return value


@pytest.fixture(autouse=True, scope="function")
def check_all_patients_change(request: pytest.FixtureRequest, api_manager: ApiManager):
    """
    Marker-driven post-action verification for API tests.
    Verifies patients count based on created person.

    Usage:
      @pytest.mark.check_all_patients_change(delta=1, person_uuid_source="create_person.uuid")
    """
    mark = request.node.get_closest_marker("check_all_patients_change")
    if not mark:
        yield
        return

    delta = int(mark.kwargs.get("delta", 0))
    person_uuid_source: Optional[str] = mark.kwargs.get("person_uuid_source")
    should_exist = mark.kwargs.get("should_exist")
    if should_exist is None:
        should_exist = delta > 0
    should_exist = bool(should_exist)

    # In xdist (or other parallel runs) global "count delta" is not stable, because other tests
    # can create/delete users between our before/after snapshots. Allow opting into strict mode.
    strict_delta = bool(mark.kwargs.get("strict_delta", False))
    running_xdist = hasattr(request.config, "workerinput")

    # Resolve username early (before yield), while parametrized args are still accessible.
    resolved_person_uuid: Optional[str] = None
    if person_uuid_source:
        resolved_person_uuid = str(_resolve_source(request, person_uuid_source))

    before = api_manager.database_steps.get_all_patients()
    before_patient_ids = {u.patient_id for u in before}
    yield
    after = api_manager.database_steps.get_all_patients()
    after_patient_ids = {u.patient_id for u in after}

    if resolved_person_uuid is not None:
        patient_id = api_manager.database_steps.get_person_by_uuid(resolved_person_uuid).person_id
        if should_exist:
            assert patient_id in after_patient_ids, (
                f"Expected patient with id '{patient_id}' existence=True in DB.patient table, "
                f"but it was not found."
            )
            # In sequential runs we can also assert the user wasn't present before (true "creation").
            if (not running_xdist) and delta > 0:
                assert patient_id not in before_patient_ids, (
                    f"Expected patient with id '{patient_id}' to be newly created, but it already existed before."
                )
        else:
            assert patient_id not in after_patient_ids, (
                f"Expected patient with id '{patient_id}' existence=False in DB.patient table, "
                f"but it was found."
            )

    # Count delta is reliable only in sequential runs (or when explicitly requested).
    if strict_delta and not running_xdist:
        assert len(after) - len(before) == delta, (
            f"Expected patients delta={delta} (after-before), but got {len(after) - len(before)}. "
            f"before={len(before)}, after={len(after)}"
        )
