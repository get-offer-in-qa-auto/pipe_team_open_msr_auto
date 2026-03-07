import json
from pathlib import Path


def load_json(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_md(summary: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# API Coverage Summary",
        "",
        f"**Total swagger operations:** {summary['total_swagger_operations']}",
        f"**Covered swagger operations:** {summary['covered_swagger_operations']}",
        f"**Coverage:** {summary['coverage_percent']}%",
        "",
        "## Matched operations",
    ]

    lines.extend(f"- {item}" for item in summary["matched_operations"])
    lines.append("")
    lines.append("## Uncovered swagger operations")
    lines.extend(f"- {item}" for item in summary["uncovered_operations"])
    lines.append("")
    lines.append("## Covered but absent in swagger")
    lines.extend(f"- {item}" for item in summary["extra_operations"])
    lines.append("")

    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def calculate_and_save_summary() -> dict:
    swagger_path = Path("artifacts/api_coverage/swagger_operations.json")
    covered_path = Path("artifacts/api_coverage/covered_operations.json")

    summary_json_path = Path("artifacts/api_coverage/api_coverage_summary.json")
    summary_md_path = Path("artifacts/api_coverage/api_coverage_summary.md")

    swagger_operations = set(load_json(swagger_path))
    covered_operations = set(load_json(covered_path))

    matched_operations = sorted(swagger_operations & covered_operations)
    uncovered_operations = sorted(swagger_operations - covered_operations)
    extra_operations = sorted(covered_operations - swagger_operations)

    total = len(swagger_operations)
    covered = len(matched_operations)
    coverage_percent = round((covered / total) * 100, 2) if total else 0.0

    summary = {
        "total_swagger_operations": total,
        "covered_swagger_operations": covered,
        "coverage_percent": coverage_percent,
        "matched_operations": matched_operations,
        "uncovered_operations": uncovered_operations,
        "extra_operations": extra_operations,
    }

    save_json(summary, summary_json_path)
    save_md(summary, summary_md_path)

    print(f"Total swagger operations: {total}")
    print(f"Covered swagger operations: {covered}")
    print(f"Coverage: {coverage_percent}%")

    print("\nMatched operations:")
    for operation in matched_operations:
        print(operation)

    print("\nUncovered swagger operations:")
    for operation in uncovered_operations:
        print(operation)

    print("\nCovered but absent in swagger:")
    for operation in extra_operations:
        print(operation)

    print(f"\nSaved JSON summary to: {summary_json_path}")
    print(f"Saved MD summary to: {summary_md_path}")

    return summary


def main() -> None:
    calculate_and_save_summary()


if __name__ == "__main__":
    main()