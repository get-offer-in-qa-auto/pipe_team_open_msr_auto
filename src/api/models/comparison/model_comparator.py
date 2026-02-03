from typing import Any, Dict, List
from dataclasses import dataclass
import re

@dataclass
class Mismatch:
    field_name: str
    expected: Any
    actual: Any

class ComparisonResult:
    def __init__(self, mismatches: List [Mismatch]):
        self._mismatches =  mismatches

    def is_success(self) -> bool:
        return not self.mismatches

    @property
    def mismatches(self)->List [Mismatch]:
        return self._mismatches

class ModelComparator:
    @staticmethod
    def compare_fields(request: Any, response: Any, field_mapping: Dict[str,str]):
        mismatches = []
        for request_field, response_field in field_mapping.items():
            request_value = ModelComparator._get_field_value(request, request_field)
            response_value = ModelComparator._get_field_value(response, response_field)
            if str(request_value)!=str(response_value):
                mismatches.append(Mismatch(f'{request_field} -> {response_field}', request_value, response_value))
        return ComparisonResult(mismatches)

    @staticmethod
    def _get_field_value(obj: Any, path: str) -> Any:
        """
        Поддерживает пути вида:
        - gender
        - names[0].givenName
        - names[0].familyName
        """
        current = obj

        for part in path.split("."):
            # names[0]
            match = re.match(r"(\w+)\[(\d+)\]", part)
            if match:
                attr_name, index = match.groups()
                index = int(index)

                # attr
                if isinstance(current, dict):
                    current = current[attr_name]
                else:
                    current = getattr(current, attr_name)

                # index
                current = current[index]
            else:
                # обычное поле
                if isinstance(current, dict):
                    current = current[part]
                else:
                    current = getattr(current, part)

        return current
