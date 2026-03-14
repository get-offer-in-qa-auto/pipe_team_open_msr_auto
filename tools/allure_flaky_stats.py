from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile


@dataclass
class RunStats:
    run_name: str
    total_tests: int
    api_tests: int
    ui_tests: int
    flaky_tests: int
    api_flaky_tests: int
    ui_flaky_tests: int
    passed_tests: int
    failed_tests: int
    broken_tests: int
    total_duration_ms: int
    api_duration_ms: int
    ui_duration_ms: int
    suite_duration_ms: int

    @property
    def flaky_percent(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.flaky_tests / self.total_tests) * 100.0

    @property
    def ui_flaky_percent(self) -> float:
        if self.ui_tests == 0:
            return 0.0
        return (self.ui_flaky_tests / self.ui_tests) * 100.0

    @property
    def api_flaky_percent(self) -> float:
        if self.api_tests == 0:
            return 0.0
        return (self.api_flaky_tests / self.api_tests) * 100.0

    @property
    def pass_percent(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100.0

    @property
    def fail_percent(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.failed_tests / self.total_tests) * 100.0

    @property
    def broken_percent(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.broken_tests / self.total_tests) * 100.0

    @property
    def avg_duration_seconds(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.total_duration_ms / self.total_tests / 1000.0

    @property
    def avg_api_duration_seconds(self) -> float:
        if self.api_tests == 0:
            return 0.0
        return self.api_duration_ms / self.api_tests / 1000.0

    @property
    def ui_duration_seconds(self) -> float:
        return self.ui_duration_ms / 1000.0

    @property
    def api_duration_seconds(self) -> float:
        return self.api_duration_ms / 1000.0

    @property
    def suite_duration_seconds(self) -> float:
        return self.suite_duration_ms / 1000.0


@dataclass
class SlowTestRecord:
    run_name: str
    test_name: str
    duration_ms: int
    status: str

    @property
    def duration_seconds(self) -> float:
        return self.duration_ms / 1000.0


def _is_flaky_from_result(payload: dict) -> bool:
    status_details = payload.get("statusDetails")
    if isinstance(status_details, dict) and status_details.get("flaky") is True:
        return True

    labels = payload.get("labels")
    if isinstance(labels, list):
        for label in labels:
            if not isinstance(label, dict):
                continue
            if str(label.get("name", "")).lower() != "flaky":
                continue
            value = str(label.get("value", "")).strip().lower()
            if value in {"true", "1", "yes"}:
                return True
    return False


def _is_flaky_from_test_case(payload: dict) -> bool:
    return payload.get("flaky") is True


def _iter_json_from_zip(zip_path: Path, suffix: str, path_part: str | None = None) -> list[dict]:
    items: list[dict] = []
    with ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if not info.filename.endswith(suffix):
                continue
            if info.is_dir():
                continue
            if path_part and path_part not in info.filename:
                continue

            try:
                with archive.open(info, "r") as f:
                    payload = json.load(f)
                if isinstance(payload, dict):
                    items.append(payload)
            except (OSError, json.JSONDecodeError):
                continue
    return items


def _extract_duration_ms(payload: dict) -> int:
    direct_duration = payload.get("duration")
    if isinstance(direct_duration, (int, float)) and direct_duration >= 0:
        return int(direct_duration)

    direct_start = payload.get("start")
    direct_stop = payload.get("stop")
    if isinstance(direct_start, (int, float)) and isinstance(direct_stop, (int, float)) and direct_stop >= direct_start:
        return int(direct_stop - direct_start)

    time_data = payload.get("time")
    if not isinstance(time_data, dict):
        return 0

    duration = time_data.get("duration")
    if isinstance(duration, (int, float)) and duration >= 0:
        return int(duration)

    start = time_data.get("start")
    stop = time_data.get("stop")
    if isinstance(start, (int, float)) and isinstance(stop, (int, float)) and stop >= start:
        return int(stop - start)
    return 0


def _extract_start_stop(payload: dict) -> tuple[int, int] | None:
    start = payload.get("start")
    stop = payload.get("stop")
    if isinstance(start, (int, float)) and isinstance(stop, (int, float)) and stop >= start:
        return int(start), int(stop)

    time_data = payload.get("time")
    if not isinstance(time_data, dict):
        return None

    start = time_data.get("start")
    stop = time_data.get("stop")
    if isinstance(start, (int, float)) and isinstance(stop, (int, float)) and stop >= start:
        return int(start), int(stop)
    return None


def _extract_test_name(payload: dict) -> str:
    for key in ("fullName", "testCaseName", "name", "uid"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown_test"


def _iter_test_payloads(zip_path: Path) -> list[dict]:
    result_items = _iter_json_from_zip(zip_path, "-result.json")
    if result_items:
        return result_items

    test_case_items = _iter_json_from_zip(zip_path, ".json", path_part="data/test-cases/")
    return [item for item in test_case_items if "status" in item and "uid" in item]


def _test_identity(payload: dict) -> str:
    for key in ("historyId", "testCaseId", "fullName", "testCaseName", "name", "uid"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown_test"


def _select_final_attempt(payloads: list[dict]) -> dict:
    def _attempt_order(payload: dict) -> tuple[int, int]:
        stop_start = _extract_start_stop(payload)
        if stop_start is not None:
            return stop_start[1], stop_start[0]
        return 0, 0

    return max(payloads, key=_attempt_order)


def collect_stats_for_zip(zip_path: Path) -> RunStats:
    payloads = _iter_test_payloads(zip_path)
    if payloads:
        grouped_payloads: dict[str, list[dict]] = {}
        for item in payloads:
            grouped_payloads.setdefault(_test_identity(item), []).append(item)

        final_payloads = [_select_final_attempt(group) for group in grouped_payloads.values()]
        total = len(final_payloads)
        api_tests = 0
        ui_tests = 0
        api_duration_ms = 0
        ui_duration_ms = 0
        duration_ms = 0
        statuses: list[str] = []
        ui_flaky_tests = 0
        api_flaky_tests = 0
        has_result_format = any("labels" in item or "statusDetails" in item for item in payloads)
        for attempts in grouped_payloads.values():
            item = _select_final_attempt(attempts)
            test_name = _extract_test_name(item).lower()
            duration = _extract_duration_ms(item)
            duration_ms += duration
            statuses.append(str(item.get("status", "")).lower())
            if has_result_format:
                is_flaky = any(_is_flaky_from_result(attempt) for attempt in attempts)
            else:
                is_flaky = any(_is_flaky_from_test_case(attempt) for attempt in attempts)
            if ".api." in test_name:
                api_tests += 1
                api_duration_ms += duration
                if is_flaky:
                    api_flaky_tests += 1
            if ".ui." in test_name:
                ui_tests += 1
                ui_duration_ms += duration
                if is_flaky:
                    ui_flaky_tests += 1
        flaky = ui_flaky_tests + api_flaky_tests
        passed = sum(1 for status in statuses if status == "passed")
        failed = sum(1 for status in statuses if status == "failed")
        broken = sum(1 for status in statuses if status == "broken")
        start_stop_values = [v for v in (_extract_start_stop(item) for item in payloads) if v is not None]
        if start_stop_values:
            min_start = min(v[0] for v in start_stop_values)
            max_stop = max(v[1] for v in start_stop_values)
            suite_duration_ms = max(0, max_stop - min_start)
        else:
            suite_duration_ms = 0
        return RunStats(
            run_name=zip_path.name,
            total_tests=total,
            api_tests=api_tests,
            ui_tests=ui_tests,
            flaky_tests=flaky,
            api_flaky_tests=api_flaky_tests,
            ui_flaky_tests=ui_flaky_tests,
            passed_tests=passed,
            failed_tests=failed,
            broken_tests=broken,
            total_duration_ms=duration_ms,
            api_duration_ms=api_duration_ms,
            ui_duration_ms=ui_duration_ms,
            suite_duration_ms=suite_duration_ms,
        )

    return RunStats(
        run_name=zip_path.name,
        total_tests=0,
        api_tests=0,
        ui_tests=0,
        flaky_tests=0,
        api_flaky_tests=0,
        ui_flaky_tests=0,
        passed_tests=0,
        failed_tests=0,
        broken_tests=0,
        total_duration_ms=0,
        api_duration_ms=0,
        ui_duration_ms=0,
        suite_duration_ms=0,
    )


def collect_slowest_tests(artifacts_dir: Path, limit: int = 20) -> list[SlowTestRecord]:
    zip_files = sorted(artifacts_dir.glob("*.zip"))
    records: list[SlowTestRecord] = []
    for path in zip_files:
        try:
            payloads = _iter_test_payloads(path)
        except BadZipFile:
            continue

        grouped_payloads: dict[str, list[dict]] = {}
        for item in payloads:
            grouped_payloads.setdefault(_test_identity(item), []).append(item)

        for attempts in grouped_payloads.values():
            item = _select_final_attempt(attempts)
            duration_ms = _extract_duration_ms(item)
            if duration_ms <= 0:
                continue
            records.append(
                SlowTestRecord(
                    run_name=path.name,
                    test_name=_extract_test_name(item),
                    duration_ms=duration_ms,
                    status=str(item.get("status", "unknown")),
                )
            )

    records.sort(key=lambda r: r.duration_ms, reverse=True)
    return records[:max(1, limit)]


def collect_all_stats(artifacts_dir: Path) -> list[RunStats]:
    zip_files = sorted(artifacts_dir.glob("*.zip"))
    rows: list[RunStats] = []
    for path in zip_files:
        try:
            rows.append(collect_stats_for_zip(path))
        except BadZipFile:
            continue
    return rows


def print_report(rows: list[RunStats]) -> None:
    if not rows:
        print("No .zip artifacts found.")
        return

    print(
        "run,total_tests,passed_tests,pass_percent,failed_tests,fail_percent,broken_tests,broken_percent,"
        "flaky_tests,flaky_percent,"
        "total_duration_ms,avg_duration_sec,suite_duration_ms,suite_duration_sec"
    )
    for row in rows:
        print(
            f"{row.run_name},{row.total_tests},{row.passed_tests},{row.pass_percent:.2f},"
            f"{row.failed_tests},{row.fail_percent:.2f},{row.broken_tests},{row.broken_percent:.2f},"
            f"{row.flaky_tests},{row.flaky_percent:.2f},{row.total_duration_ms},{row.avg_duration_seconds:.2f},"
            f"{row.suite_duration_ms},{row.suite_duration_seconds:.2f}"
        )

    total_tests = sum(row.total_tests for row in rows)
    total_passed = sum(row.passed_tests for row in rows)
    total_failed = sum(row.failed_tests for row in rows)
    total_broken = sum(row.broken_tests for row in rows)
    total_flaky = sum(row.flaky_tests for row in rows)
    total_duration_ms = sum(row.total_duration_ms for row in rows)
    total_suite_duration_ms = sum(row.suite_duration_ms for row in rows)
    total_pass_percent = (total_passed / total_tests * 100.0) if total_tests else 0.0
    total_fail_percent = (total_failed / total_tests * 100.0) if total_tests else 0.0
    total_broken_percent = (total_broken / total_tests * 100.0) if total_tests else 0.0
    total_percent = (total_flaky / total_tests * 100.0) if total_tests else 0.0
    total_avg_duration_sec = (total_duration_ms / total_tests / 1000.0) if total_tests else 0.0
    print(
        f"TOTAL,{total_tests},{total_passed},{total_pass_percent:.2f},"
        f"{total_failed},{total_fail_percent:.2f},{total_broken},{total_broken_percent:.2f},"
        f"{total_flaky},{total_percent:.2f},"
        f"{total_duration_ms},{total_avg_duration_sec:.2f},{total_suite_duration_ms},{total_suite_duration_ms / 1000.0:.2f}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect flaky tests statistics from downloaded Allure report/artifact zip files."
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("downloaded_artifacts"),
        help="Directory containing downloaded .zip artifacts (default: downloaded_artifacts).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts_dir: Path = args.artifacts_dir
    if not artifacts_dir.exists() or not artifacts_dir.is_dir():
        print(f"Artifacts directory not found: {artifacts_dir}")
        return 1

    rows = collect_all_stats(artifacts_dir)
    print_report(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
