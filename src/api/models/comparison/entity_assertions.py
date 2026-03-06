from __future__ import annotations

from typing import Any


class EntityAssertions:
    @staticmethod
    def has_uuid(entity: Any, field: str = "uuid") -> Any:
        value = getattr(entity, field, None)
        assert value, f"{entity.__class__.__name__}.{field} is falsy: {entity}"
        assert str(value).lower() != "null", f"{entity.__class__.__name__}.{field} returned as 'null': {entity}"
        return entity

    @staticmethod
    def has_display(entity: Any, field: str = "display") -> Any:
        value = getattr(entity, field, None)
        assert value, f"{entity.__class__.__name__}.{field} is falsy: {entity}"
        return entity
