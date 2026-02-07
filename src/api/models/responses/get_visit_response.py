from __future__ import annotations

from src.api.models.responses.create_visit_response import VisitCreateResponse


class VisitFullResponse(VisitCreateResponse):
    """GET /visit/{uuid}?v=full

    По полям нам достаточно того же набора, что и для create response.
    (остальные поля OpenMRS просто проигнорируются pydantic-ом)
    """
    pass