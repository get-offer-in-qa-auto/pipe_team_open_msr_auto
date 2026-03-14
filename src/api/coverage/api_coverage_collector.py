import json
from pathlib import Path


class ApiCoverageCollector:
    _operations: set[str] = set()

    @classmethod
    def record(cls, method: str, path: str) -> None:
        cls._operations.add(f"{method.upper()} {path}")

    @classmethod
    def save(cls, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(sorted(cls._operations), f, indent=2, ensure_ascii=False)