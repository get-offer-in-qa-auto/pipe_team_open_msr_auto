import json
from pathlib import Path
from typing import Iterable

HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


def load_swagger(swagger_path: Path) -> dict:
    with swagger_path.open(encoding="utf-8") as f:
        return json.load(f)


def get_root_resource(path: str) -> str:
    return path.lstrip("/").split("/")[0]


def extract_operations(swagger: dict, resources: Iterable[str]) -> list[str]:
    resources_set = set(resources)
    operations = set()

    for path, path_item in swagger.get("paths", {}).items():
        root_resource = get_root_resource(path)
        if root_resource not in resources_set:
            continue

        for method in path_item.keys():
            method_lower = method.lower()
            if method_lower not in HTTP_METHODS:
                continue

            operations.add(f"{method_lower.upper()} {path}")

    return sorted(operations)


def save_operations(operations: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(operations, f, indent=2, ensure_ascii=False)


def generate_swagger_operations() -> list[str]:
    swagger_path = Path("resources/swagger.json")
    output_path = Path("artifacts/api_coverage/swagger_operations.json")
    scope_resources = ["person", "provider", "user", "encounter"]

    swagger = load_swagger(swagger_path)
    operations = extract_operations(swagger, scope_resources)
    save_operations(operations, output_path)
    return operations


def main() -> None:
    operations = generate_swagger_operations()

    print("Swagger operations in scope:")
    for operation in operations:
        print(operation)

    print(f"\nTotal operations: {len(operations)}")
    print("Saved to: artifacts/api_coverage/swagger_operations.json")


if __name__ == "__main__":
    main()
