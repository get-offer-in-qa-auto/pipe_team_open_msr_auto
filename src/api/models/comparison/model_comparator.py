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
    def compare_fields(request: Any, response: Any, field_mapping: Dict[str, str]):
        mismatches = []
        for request_field, response_field in field_mapping.items():
            request_value = ModelComparator._get_field_value(request, request_field)

            # ✅ partial update: None = поле не передавали → не сравниваем
            if request_value is None:
                continue

            response_value = ModelComparator._get_field_value(response, response_field)

            exp = ModelComparator._normalize_value(request_value)
            act = ModelComparator._normalize_value(response_value)

            if exp != act:
                mismatches.append(
                    Mismatch(f"{request_field} -> {response_field}", request_value, response_value)
                )

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

    @staticmethod
    def _normalize_value(value: Any) -> str:
        if value is None:
            return ""

        s = str(value).strip()

        # ✅ normalize gender UI -> API
        gender_map = {
            "male": "M",
            "female": "F",
            "unknown": "U",
            "other": "U",
        }
        low = s.lower()
        if low in gender_map:
            return gender_map[low]

        # also allow API -> API passthrough
        if s in ("M", "F", "U"):
            return s

        # ISO date/datetime → compare only date
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":
            return s[:10]

        return s
