from __future__ import annotations
import allure

from typing import Any


class EntityAssertions:
    @staticmethod
    @allure.step("has_uuid")
    def has_uuid(entity: Any, field: str = "uuid") -> Any:
        value = getattr(entity, field, None)
        assert value, f"{entity.__class__.__name__}.{field} is falsy: {entity}"
        assert str(value).lower() != "null", f"{entity.__class__.__name__}.{field} returned as 'null': {entity}"
        return entity

    @staticmethod
    @allure.step("has_display")
    def has_display(entity: Any, field: str = "display") -> Any:
        value = getattr(entity, field, None)
        assert value, f"{entity.__class__.__name__}.{field} is falsy: {entity}"
        return entity
