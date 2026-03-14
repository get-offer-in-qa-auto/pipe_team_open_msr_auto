from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from allure_flaky_stats import RunStats, collect_all_stats, collect_slowest_tests

DEFAULT_GATES: dict[str, dict[str, Any]] = {
    "pass_rate":
        {
            "name": "Pass Rate",
            "unit": "%",
            "good_threshold": 98.0,
            "warn_threshold": 95.0,
            "higher_is_better": True,
            "recommendation": "Review failing tests and fix frequent assertions.",
        },
    "fail_rate":
        {
            "name": "Fail Rate",
            "unit": "%",
            "good_threshold": 2.0,
            "warn_threshold": 5.0,
            "higher_is_better": False,
            "recommendation": "Prioritize top failing suites and stabilize environments.",
        },
    "broken_rate":
        {
            "name": "Broken Rate",
            "unit": "%",
            "good_threshold": 1.0,
            "warn_threshold": 3.0,
            "higher_is_better": False,
            "recommendation": "Fix infrastructure/test setup errors first.",
        },
    "flaky_rate":
        {
            "name": "Flaky Rate",
            "unit": "%",
            "good_threshold": 2.0,
            "warn_threshold": 5.0,
            "higher_is_better": False,
            "recommendation": "Quarantine flaky tests and remove unstable waits.",
        },
    "stability_rate":
        {
            "name": "Test Stability",
            "unit": "%",
            "good_threshold": 95.0,
            "warn_threshold": 85.0,
            "higher_is_better": True,
            "recommendation": "Track unstable runs and fix recurring root causes.",
        },
    "avg_duration_sec":
        {
            "name": "Average Test Duration UI tests",
            "unit": "s",
            "good_threshold": 3.0,
            "warn_threshold": 5.0,
            "higher_is_better": False,
            "recommendation": "Optimize slow tests and reduce external dependencies.",
        },
    "avg_api_duration_sec":
        {
            "name": "Average Test Duration API tests",
            "unit": "s",
            "good_threshold": 0.2,
            "warn_threshold": 0.35,
            "higher_is_better": False,
            "recommendation": "Optimize slow API tests and reduce network/DB overhead.",
        },
    "ui_run_duration_sec":
        {
            "name": "Average UI Test Run Duration",
            "unit": "s",
            "good_threshold": 240.0,
            "warn_threshold": 360.0,
            "higher_is_better": False,
            "recommendation": "Reduce end-to-end UI runtime with better parallelization and setup reuse.",
        },
    "api_run_duration_sec":
        {
            "name": "Average API Test Run Duration",
            "unit": "s",
            "good_threshold": 20.0,
            "warn_threshold": 30.0,
            "higher_is_better": False,
            "recommendation": "Optimize API request/DB paths and trim heavy setup per run.",
        },
    "suite_duration_sec":
        {
            "name": "CI Pipeline Duration (proxy)",
            "unit": "s",
            "good_threshold": 240.0,
            "warn_threshold": 360.0,
            "higher_is_better": False,
            "recommendation": "Increase parallelism and remove long serial bottlenecks.",
        },
}
DEFAULT_SLOWEST_TESTS_LIMIT = 4


def load_dashboard_config(config_path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    gates = copy.deepcopy(DEFAULT_GATES)
    slowest_tests_limit = DEFAULT_SLOWEST_TESTS_LIMIT
    if not config_path.exists():
        legacy_path = Path("metrics_gates.yml")
        if legacy_path.exists():
            config_path = legacy_path
        else:
            print(f"Gates config not found, using defaults: {config_path}")
            return gates, slowest_tests_limit
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"Failed to read gates config ({config_path}): {exc}. Using defaults.")
        return gates, slowest_tests_limit

    report_cfg = raw.get("report")
    if isinstance(report_cfg, dict):
        raw_limit = report_cfg.get("slowest_tests_limit")
        if isinstance(raw_limit, int) and raw_limit > 0:
            slowest_tests_limit = raw_limit

    user_gates = raw.get("gates")
    if not isinstance(user_gates, dict):
        print(f"Invalid gates config format in {config_path}, expected 'gates' mapping. Using defaults.")
        return gates, slowest_tests_limit

    allowed_fields = {
        "name",
        "unit",
        "good_threshold",
        "warn_threshold",
        "higher_is_better",
        "recommendation",
    }
    for key, user_value in user_gates.items():
        if key not in gates or not isinstance(user_value, dict):
            continue
        for field_name, field_value in user_value.items():
            if field_name in allowed_fields:
                gates[key][field_name] = field_value
    return gates, slowest_tests_limit


def parse_run_datetime(run_name: str) -> datetime | None:
    match = re.match(r"^(?P<date>\d{8})_(?P<time>\d{6})_", run_name)
    if not match:
        return None
    try:
        return datetime.strptime(f"{match.group('date')}_{match.group('time')}", "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def fmt_datetime(dt: datetime | None, fallback: str) -> str:
    if dt is None:
        return fallback
    return dt.strftime("%Y-%m-%d %H:%M")


def evaluate_gate(value: float, good_threshold: float, warn_threshold: float, higher_is_better: bool) -> str:
    del warn_threshold
    if higher_is_better:
        return "ok" if value >= good_threshold else "fail"
    return "ok" if value <= good_threshold else "fail"


def build_gate(
    key: str,
    name: str,
    value: float,
    unit: str,
    good_threshold: float,
    warn_threshold: float,
    higher_is_better: bool,
    formula: str,
    recommendation: str,
) -> dict:
    status = evaluate_gate(value, good_threshold, warn_threshold, higher_is_better)
    threshold = f">= {good_threshold:.2f}{unit}" if higher_is_better else f"<= {good_threshold:.2f}{unit}"
    status_label = {"ok": "OK", "fail": "Failed"}[status]
    css_class = {"ok": "metric-ok", "fail": "metric-fail"}[status]
    return {
        "key": key,
        "name": name,
        "value": value,
        "unit": unit,
        "status": status,
        "status_label": status_label,
        "css_class": css_class,
        "threshold": threshold,
        "formula": formula,
        "recommendation": recommendation,
    }


def build_html(
    report_title: str,
    rows: list[RunStats],
    slowest_ui_tests: list[dict],
    slowest_api_tests: list[dict],
    gates_config: dict[str, dict[str, Any]],
) -> str:
    sorted_rows = sorted(rows, key=lambda r: parse_run_datetime(r.run_name) or datetime.min)
    distribution_gate_keys = ["pass_rate", "fail_rate", "broken_rate"]

    points: list[dict] = []
    for row in sorted_rows:
        run_dt = parse_run_datetime(row.run_name)
        run_success = row.total_tests > 0 and row.passed_tests == row.total_tests
        run_values = {
            "pass_rate": row.pass_percent,
            "fail_rate": row.fail_percent,
            "broken_rate": row.broken_percent,
        }
        run_qg_passed = 0
        for key in distribution_gate_keys:
            cfg = gates_config.get(key, DEFAULT_GATES[key])
            gate_status = evaluate_gate(
                value=float(run_values[key]),
                good_threshold=float(cfg["good_threshold"]),
                warn_threshold=float(cfg["warn_threshold"]),
                higher_is_better=bool(cfg["higher_is_better"]),
            )
            if gate_status == "ok":
                run_qg_passed += 1
        run_qg_failed = len(distribution_gate_keys) - run_qg_passed
        run_qg_status = "OK" if run_qg_failed == 0 else "Failed"
        run_qg_css_class = "metric-ok" if run_qg_failed == 0 else "metric-fail"
        points.append(
            {
                "run_name": row.run_name,
                "run_label": fmt_datetime(run_dt, row.run_name),
                "total_tests": row.total_tests,
                "passed_tests": row.passed_tests,
                "pass_percent": round(row.pass_percent, 2),
                "failed_tests": row.failed_tests,
                "fail_percent": round(row.fail_percent, 2),
                "broken_tests": row.broken_tests,
                "broken_percent": round(row.broken_percent, 2),
                "flaky_tests": row.flaky_tests,
                "flaky_percent": round(row.flaky_percent, 2),
                "ui_flaky_percent": round(row.ui_flaky_percent, 2),
                "api_flaky_percent": round(row.api_flaky_percent, 2),
                "run_success": run_success,
                "stability_value": 100.0 if run_success else 0.0,
                "run_qg_passed": run_qg_passed,
                "run_qg_failed": run_qg_failed,
                "run_qg_status": run_qg_status,
                "run_qg_css_class": run_qg_css_class,
                "total_duration_ms": row.total_duration_ms,
                "avg_duration_sec": round(row.avg_duration_seconds, 2),
                "avg_api_duration_sec": round(row.avg_api_duration_seconds, 2),
                "ui_run_duration_sec": round(row.ui_duration_seconds, 2),
                "api_run_duration_sec": round(row.api_duration_seconds, 2),
                "suite_duration_ms": row.suite_duration_ms,
                "suite_duration_sec": round(row.suite_duration_seconds, 2),
            }
        )

    total_runs = len(rows)
    total_tests = sum(r.total_tests for r in rows)
    total_flaky = sum(r.flaky_tests for r in rows)
    successful_runs = sum(1 for r in rows if r.total_tests > 0 and r.passed_tests == r.total_tests)

    flaky_rate = round((total_flaky / total_tests * 100.0), 2) if total_tests else 0.0
    stability_rate = round((successful_runs / total_runs * 100.0), 2) if total_runs else 0.0

    avg_pass_rate = round((sum(r.pass_percent for r in rows) / total_runs), 2) if total_runs else 0.0
    avg_fail_rate = round((sum(r.fail_percent for r in rows) / total_runs), 2) if total_runs else 0.0
    avg_broken_rate = round((sum(r.broken_percent for r in rows) / total_runs), 2) if total_runs else 0.0
    avg_ui_flaky_rate = round((sum(r.ui_flaky_percent for r in rows) / total_runs), 2) if total_runs else 0.0
    avg_api_flaky_rate = round((sum(r.api_flaky_percent for r in rows) / total_runs), 2) if total_runs else 0.0

    avg_duration_sec = round((sum(r.avg_duration_seconds for r in rows) / total_runs), 2) if total_runs else 0.0
    avg_api_duration_sec = round((sum(r.avg_api_duration_seconds for r in rows) / total_runs), 2) if total_runs else 0.0
    ui_run_duration_sec = round((sum(r.ui_duration_seconds for r in rows) / total_runs), 2) if total_runs else 0.0
    api_run_duration_sec = round((sum(r.api_duration_seconds for r in rows) / total_runs), 2) if total_runs else 0.0
    avg_suite_duration_sec = round((sum(r.suite_duration_seconds for r in rows) / total_runs), 2) if total_runs else 0.0

    pass_series = " + ".join(f"{r.pass_percent:.2f}" for r in sorted_rows)
    fail_series = " + ".join(f"{r.fail_percent:.2f}" for r in sorted_rows)
    broken_series = " + ".join(f"{r.broken_percent:.2f}" for r in sorted_rows)
    ui_flaky_series = " + ".join(f"{r.ui_flaky_percent:.2f}" for r in sorted_rows)
    api_flaky_series = " + ".join(f"{r.api_flaky_percent:.2f}" for r in sorted_rows)
    avg_pass_formula = (
        f"average pass rate = ({pass_series}) / {total_runs} = {avg_pass_rate:.2f}%"
        if total_runs else "average pass rate = n/a"
    )
    avg_fail_formula = (
        f"average fail rate = ({fail_series}) / {total_runs} = {avg_fail_rate:.2f}%"
        if total_runs else "average fail rate = n/a"
    )
    avg_broken_formula = (
        f"average broken rate = ({broken_series}) / {total_runs} = {avg_broken_rate:.2f}%"
        if total_runs else "average broken rate = n/a"
    )
    avg_ui_flaky_formula = (
        f"average UI flaky rate = ({ui_flaky_series}) / {total_runs} = {avg_ui_flaky_rate:.2f}%"
        if total_runs else "average UI flaky rate = n/a"
    )
    avg_api_flaky_formula = (
        f"average API flaky rate = ({api_flaky_series}) / {total_runs} = {avg_api_flaky_rate:.2f}%"
        if total_runs else "average API flaky rate = n/a"
    )
    avg_duration_series = " + ".join(f"{r.avg_duration_seconds:.2f}" for r in sorted_rows)

    avg_api_duration_series = " + ".join(f"{r.avg_api_duration_seconds:.2f}" for r in sorted_rows)
    ui_run_duration_series = " + ".join(f"{r.ui_duration_seconds:.2f}" for r in sorted_rows)
    api_run_duration_series = " + ".join(f"{r.api_duration_seconds:.2f}" for r in sorted_rows)
    avg_suite_duration_series = " + ".join(f"{r.suite_duration_seconds:.2f}" for r in sorted_rows)

    formulas = {
        "pass_rate":
            avg_pass_formula,
        "fail_rate":
            avg_fail_formula,
        "broken_rate":
            avg_broken_formula,
        "flaky_rate":
            f"{total_flaky}/{total_tests}={flaky_rate:.2f}%" if total_tests else "0/0=0.00%",
        "ui_flaky_rate":
            avg_ui_flaky_formula,
        "api_flaky_rate":
            avg_api_flaky_formula,
        "stability_rate":
            f"{successful_runs}/{total_runs}={stability_rate:.2f}%" if total_runs else "0/0=0.00%",
        "avg_duration_sec": (f"({avg_duration_series})/{total_runs}={avg_duration_sec:.2f}s" if total_runs else "n/a"),
        "avg_api_duration_sec":
            (f"({avg_api_duration_series})/{total_runs}={avg_api_duration_sec:.2f}s" if total_runs else "n/a"),
        "ui_run_duration_sec":
            (f"({ui_run_duration_series})/{total_runs}={ui_run_duration_sec:.2f}s" if total_runs else "n/a"),
        "api_run_duration_sec":
            (f"({api_run_duration_series})/{total_runs}={api_run_duration_sec:.2f}s" if total_runs else "n/a"),
        "suite_duration_sec":
            (f"({avg_suite_duration_series})/{total_runs}={avg_suite_duration_sec:.2f}s" if total_runs else "n/a"),
    }
    values = {
        "pass_rate": avg_pass_rate,
        "fail_rate": avg_fail_rate,
        "broken_rate": avg_broken_rate,
        "flaky_rate": flaky_rate,
        "stability_rate": stability_rate,
        "avg_duration_sec": avg_duration_sec,
        "avg_api_duration_sec": avg_api_duration_sec,
        "ui_run_duration_sec": ui_run_duration_sec,
        "api_run_duration_sec": api_run_duration_sec,
        "suite_duration_sec": avg_suite_duration_sec,
    }
    gate_name_overrides = {
        "pass_rate": "Average Pass Rate",
        "fail_rate": "Average Fail Rate",
        "broken_rate": "Average Broken Rate",
        "suite_duration_sec": "Average Pipeline Duration",
    }
    gates = []
    for key in DEFAULT_GATES.keys():
        cfg = gates_config.get(key, DEFAULT_GATES[key])
        gates.append(
            build_gate(
                key=key,
                name=gate_name_overrides.get(key, str(cfg["name"])),
                value=float(values[key]),
                unit=str(cfg["unit"]),
                good_threshold=float(cfg["good_threshold"]),
                warn_threshold=float(cfg["warn_threshold"]),
                higher_is_better=bool(cfg["higher_is_better"]),
                formula=formulas[key],
                recommendation=str(cfg["recommendation"]),
            )
        )
    flaky_cfg = gates_config.get("flaky_rate", DEFAULT_GATES["flaky_rate"])
    gates.append(
        build_gate(
            key="ui_flaky_rate",
            name="Average UI Flaky Rate",
            value=float(avg_ui_flaky_rate),
            unit=str(flaky_cfg["unit"]),
            good_threshold=float(flaky_cfg["good_threshold"]),
            warn_threshold=float(flaky_cfg["warn_threshold"]),
            higher_is_better=bool(flaky_cfg["higher_is_better"]),
            formula=formulas["ui_flaky_rate"],
            recommendation=str(flaky_cfg["recommendation"]),
        )
    )
    gates.append(
        build_gate(
            key="api_flaky_rate",
            name="Average API Flaky Rate",
            value=float(avg_api_flaky_rate),
            unit=str(flaky_cfg["unit"]),
            good_threshold=float(flaky_cfg["good_threshold"]),
            warn_threshold=float(flaky_cfg["warn_threshold"]),
            higher_is_better=bool(flaky_cfg["higher_is_better"]),
            formula=formulas["api_flaky_rate"],
            recommendation=str(flaky_cfg["recommendation"]),
        )
    )
    gate_by_key = {item["key"]: item for item in gates}

    metric_descriptions = {
        "pass_rate": "Average share of passed tests across all runs in the selected period.",
        "fail_rate": "Average share of failed tests across all runs in the selected period.",
        "broken_rate": "Average share of broken tests across all runs in the selected period.",
        "flaky_rate": "Share of flaky tests that behave inconsistently across runs.",
        "ui_flaky_rate": "Average share of flaky UI tests across all runs in the selected period.",
        "api_flaky_rate": "Average share of flaky API tests across all runs in the selected period.",
        "stability_rate": "Share of successful runs among all runs.",
        "avg_duration_sec": "Average Test Duration UI tests = Sum(run average durations) / Number of runs",
        "avg_api_duration_sec": "Average Test Duration API tests = Sum(run average API durations) / Number of runs",
        "ui_run_duration_sec": "Average UI Test Run Duration = Sum(UI run durations) / Number of runs",
        "api_run_duration_sec": "Average API Test Run Duration = Sum(API run durations) / Number of runs",
        "suite_duration_sec": "CI Pipeline Duration = build + deploy + tests",
    }

    def build_section_gates(
        keys: list[str],
        include_action: bool = True,
        include_description: bool = False,
        action_as_description: bool = False,
        include_calculation: bool = True,
        description_after_metric: bool = False
    ) -> tuple[int, int, str]:
        section_gates = [gate_by_key[key] for key in keys]
        ok_count = sum(1 for item in section_gates if item["status"] == "ok")
        fail_count = sum(1 for item in section_gates if item["status"] == "fail")
        if include_action:
            rows_html = "\n".join(
                (
                    (
                        "<tr>" + f"<td>{item['name']}</td>" +
                        f"<td>{metric_descriptions.get(item['key'], 'Metric definition is not set.') if action_as_description else item['recommendation']}</td>"
                        + f"<td>{item['value']:.2f}{item['unit']}</td>" + f"<td>{item['threshold']}</td>" +
                        f"<td><span class=\"status-badge {item['css_class']}\">{item['status_label']}</span></td>" +
                        (f"<td>{item['formula']}</td>" if include_calculation else "") + "</tr>"
                    ) if description_after_metric else (
                        "<tr>" + f"<td>{item['name']}</td>" + f"<td>{item['value']:.2f}{item['unit']}</td>" +
                        f"<td>{item['threshold']}</td>" +
                        f"<td><span class=\"status-badge {item['css_class']}\">{item['status_label']}</span></td>" +
                        (f"<td>{item['formula']}</td>" if include_calculation else "") + (
                            f"<td>{metric_descriptions.get(item['key'], 'Metric definition is not set.') if action_as_description else item['recommendation']}</td>"
                        ) + "</tr>"
                    )
                ) for item in section_gates
            )
        elif include_description:
            rows_html = "\n".join(
                (
                    "<tr>"
                    f"<td>{item['name']}</td>"
                    f"<td>{metric_descriptions.get(item['key'], 'Metric definition is not set.')}</td>"
                    f"<td>{item['value']:.2f}{item['unit']}</td>"
                    f"<td>{item['threshold']}</td>"
                    f"<td><span class=\"status-badge {item['css_class']}\">{item['status_label']}</span></td>"
                    "</tr>"
                ) for item in section_gates
            )
        else:
            rows_html = "\n".join(
                (
                    "<tr>"
                    f"<td>{item['name']}</td>"
                    f"<td>{item['value']:.2f}{item['unit']}</td>"
                    f"<td>{item['threshold']}</td>"
                    f"<td><span class=\"status-badge {item['css_class']}\">{item['status_label']}</span></td>"
                    f"<td>{item['formula']}</td>"
                    "</tr>"
                ) for item in section_gates
            )
        return ok_count, fail_count, rows_html

    _, _, dist_rows_html = build_section_gates(
        ["pass_rate", "fail_rate", "broken_rate", "ui_flaky_rate", "api_flaky_rate"],
        include_action=False,
        include_description=True,
    )
    speed_gate_keys = [
        "avg_duration_sec",
        "avg_api_duration_sec",
        "ui_run_duration_sec",
        "api_run_duration_sec",
        "suite_duration_sec",
    ]
    speed_ok, speed_fail, speed_rows_html = build_section_gates(
        speed_gate_keys,
        action_as_description=True,
        include_calculation=False,
        description_after_metric=True,
    )
    speed_formulas_html = "<br/>".join(
        f"{gate_by_key[key]['name']} = {gate_by_key[key]['formula']}" for key in speed_gate_keys
    )
    pass_rate_target = float(gates_config.get("pass_rate", DEFAULT_GATES["pass_rate"])["good_threshold"])
    fail_rate_target = float(gates_config.get("fail_rate", DEFAULT_GATES["fail_rate"])["good_threshold"])
    broken_rate_target = float(gates_config.get("broken_rate", DEFAULT_GATES["broken_rate"])["good_threshold"])
    flaky_rate_target = float(gates_config.get("flaky_rate", DEFAULT_GATES["flaky_rate"])["good_threshold"])
    slow_ui_target_sec = float(
        gates_config.get("avg_duration_sec", DEFAULT_GATES["avg_duration_sec"])["good_threshold"]
    )
    slow_api_target_sec = float(
        gates_config.get("avg_api_duration_sec", DEFAULT_GATES["avg_api_duration_sec"])["good_threshold"]
    )
    ui_run_target_sec = float(
        gates_config.get("ui_run_duration_sec", DEFAULT_GATES["ui_run_duration_sec"])["good_threshold"]
    )
    api_run_target_sec = float(
        gates_config.get("api_run_duration_sec", DEFAULT_GATES["api_run_duration_sec"])["good_threshold"]
    )
    pipeline_target_sec = float(
        gates_config.get("suite_duration_sec", DEFAULT_GATES["suite_duration_sec"])["good_threshold"]
    )

    pass_rate_class = gate_by_key["pass_rate"]["css_class"]
    fail_rate_class = gate_by_key["fail_rate"]["css_class"]
    broken_rate_class = gate_by_key["broken_rate"]["css_class"]
    ui_flaky_rate_class = "metric-ok" if avg_ui_flaky_rate <= flaky_rate_target else "metric-fail"
    api_flaky_rate_class = "metric-ok" if avg_api_flaky_rate <= flaky_rate_target else "metric-fail"
    avg_duration_class = gate_by_key["avg_duration_sec"]["css_class"]
    avg_api_duration_class = gate_by_key["avg_api_duration_sec"]["css_class"]
    ui_run_duration_class = gate_by_key["ui_run_duration_sec"]["css_class"]
    api_run_duration_class = gate_by_key["api_run_duration_sec"]["css_class"]
    suite_duration_class = gate_by_key["suite_duration_sec"]["css_class"]

    points_json = json.dumps(points, ensure_ascii=False)
    slowest_ui_json = json.dumps(slowest_ui_tests, ensure_ascii=False)
    slowest_api_json = json.dumps(slowest_api_tests, ensure_ascii=False)
    report_title_safe = report_title.replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>{report_title_safe}</title>
  <style>
    :root {{
      --bg0: #f4efe7;
      --bg1: #fffdf8;
      --ink: #18212f;
      --muted: #5e6b7a;
      --line: #d8d2c7;
      --card: #ffffffcc;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 400px at 0% 0%, #f0e3cf 10%, transparent 70%),
        radial-gradient(900px 500px at 100% 100%, #dceeea 10%, transparent 65%),
        var(--bg0);
    }}
    .wrap {{ max-width: 1220px; margin: 0 auto; padding: 28px 20px 48px; }}
    .title {{ margin: 0; font-size: clamp(26px, 4vw, 42px); letter-spacing: 0.01em; }}
    .subtitle {{ margin: 8px 0 0; color: var(--muted); font-size: 15px; }}
    .summary {{ display: grid; gap: 14px; margin-top: 18px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px 16px;
      backdrop-filter: blur(4px);
      box-shadow: 0 10px 28px rgba(24, 33, 47, 0.07);
    }}
    .metric-ok {{ border-color: #1c8a56; background: #f1fbf5; }}
    .metric-fail {{ border-color: #b43737; background: #fff1f1; }}
    .status-badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-weight: 700;
    }}
    .status-badge.metric-ok {{ color: #0d6e42; }}
    .status-badge.metric-fail {{ color: #8f2424; }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .value {{ margin-top: 6px; font-size: 30px; font-weight: 700; line-height: 1; }}

    .group {{
      margin-top: 18px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fffefb;
      box-shadow: 0 10px 22px rgba(24, 33, 47, 0.05);
    }}
    .group h2 {{ margin: 0; font-size: 24px; }}
    .group .desc {{ margin: 6px 0 0; color: #465463; font-size: 14px; }}
    .formulas {{ margin-top: 10px; font-size: 13px; color: #4f5d6c; line-height: 1.5; }}
    .metric-cards {{ display: grid; gap: 14px; margin-top: 14px; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }}

    .panel {{
      background: var(--bg1);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      margin-top: 16px;
      box-shadow: 0 14px 30px rgba(24, 33, 47, 0.08);
    }}
    .panel h3 {{ margin: 0 0 10px; font-size: 18px; }}
    .charts-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }}
    .metric-pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }}
    .chart-single {{ margin-top: 16px; }}

    canvas {{ width: 100%; height: 340px; display: block; }}
    .legend {{ display: flex; gap: 12px; margin-top: 8px; color: #4a5665; font-size: 13px; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; transform: translateY(1px); }}

    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: #fff; border-radius: 12px; overflow: hidden; font-size: 14px; }}
    th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid #eee9df; }}
    th {{ background: #f9f6f0; font-weight: 600; color: #3f4a57; }}
    tr:hover td {{ background: #fffbf4; }}
    .slow-tests-table {{ table-layout: fixed; }}
    .slow-tests-table th:nth-child(2), .slow-tests-table td:nth-child(2) {{
      width: 58%;
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}

    @media (max-width: 960px) {{
      .charts-2 {{ grid-template-columns: 1fr; }}
      .metric-pair {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1 class=\"title\">{report_title_safe}</h1>
    <p class=\"subtitle\">Quality metrics across GitHub runs (Allure artifacts)</p>

    <div class=\"summary\">
      <div class=\"card\"><div class=\"label\">Total Runs</div><div class=\"value\">{total_runs}</div></div>
      <div class=\"card\"><div class=\"label\">Generated Metric Groups</div><div class=\"value\">3</div></div>
    </div>

    <section class=\"group\">
      <h2>1️⃣ Test Result Distribution</h2>
      <p class=\"desc\">Distribution of test outcomes by status.</p>
      <div class=\"panel\">
        <h3>🚦 Quality Gates</h3>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Description</th>
              <th>Current Value</th>
              <th>Target</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {dist_rows_html}
          </tbody>
        </table>
      </div>
      <div class=\"metric-cards\">
        <div class=\"card {pass_rate_class}\"><div class=\"label\">average pass rate</div><div class=\"value\">{avg_pass_rate:.2f}%</div></div>
        <div class=\"card {fail_rate_class}\"><div class=\"label\">average fail rate</div><div class=\"value\">{avg_fail_rate:.2f}%</div></div>
        <div class=\"card {broken_rate_class}\"><div class=\"label\">average broken rate</div><div class=\"value\">{avg_broken_rate:.2f}%</div></div>
        <div class=\"card {ui_flaky_rate_class}\"><div class=\"label\">average UI flaky rate</div><div class=\"value\">{avg_ui_flaky_rate:.2f}%</div></div>
        <div class=\"card {api_flaky_rate_class}\"><div class=\"label\">average API flaky rate</div><div class=\"value\">{avg_api_flaky_rate:.2f}%</div></div>
      </div>

      <div class=\"panel\">
        <h3>How Metrics Are Calculated</h3>
        <div class=\"formulas\">
          {avg_pass_formula}<br/>
          {avg_fail_formula}<br/>
          {avg_broken_formula}<br/>
          {avg_ui_flaky_formula}<br/>
          {avg_api_flaky_formula}
        </div>
      </div>

      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average Pass Rate Trend</h3>
          <canvas id=\"pass-rate-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Pass Rate vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Pass %</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"pass-distribution-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average Fail Rate Trend</h3>
          <canvas id=\"fail-rate-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Fail Rate vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Fail %</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"fail-distribution-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average Broken Rate Trend</h3>
          <canvas id=\"broken-rate-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Broken Rate vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Broken %</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"broken-distribution-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average UI Flaky Rate Trend</h3>
          <canvas id=\"ui-flaky-rate-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>UI Flaky Rate vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>UI Flaky %</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"ui-flaky-distribution-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average API Flaky Rate Trend</h3>
          <canvas id=\"api-flaky-rate-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>API Flaky Rate vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>API Flaky %</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"api-flaky-distribution-rows\"></tbody>
          </table>
        </div>
      </div>
    </section>

    <section class=\"group\">
      <h2>2️⃣ Speed Metrics</h2>
      <p class=\"desc\">Show how fast the pipeline is. CI Pipeline Duration is currently estimated from available test runtime data.</p>
      <div class=\"panel\">
        <h3>🚦 Quality Gates</h3>
        <div class=\"metric-cards\">
          <div class=\"card metric-ok\"><div class=\"label\">OK Gates</div><div class=\"value\">{speed_ok}</div></div>
          <div class=\"card metric-fail\"><div class=\"label\">Failed Gates</div><div class=\"value\">{speed_fail}</div></div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Description</th>
              <th>Current Value</th>
              <th>Target</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {speed_rows_html}
          </tbody>
        </table>
      </div>
      <div class=\"panel\">
        <h3>How Metrics Are Calculated</h3>
        <div class=\"formulas\">
          {speed_formulas_html}
        </div>
      </div>
      <div class=\"metric-cards\">
        <div class=\"card {avg_duration_class}\"><div class=\"label\">Average Test Duration UI tests</div><div class=\"value\">{avg_duration_sec:.2f}s</div></div>
        <div class=\"card {avg_api_duration_class}\"><div class=\"label\">Average Test Duration API tests</div><div class=\"value\">{avg_api_duration_sec:.2f}s</div></div>
        <div class=\"card {ui_run_duration_class}\"><div class=\"label\">Average UI Test Run Duration</div><div class=\"value\">{ui_run_duration_sec:.2f}s</div></div>
        <div class=\"card {api_run_duration_class}\"><div class=\"label\">Average API Test Run Duration</div><div class=\"value\">{api_run_duration_sec:.2f}s</div></div>
        <div class=\"card {suite_duration_class}\"><div class=\"label\">Average Pipeline Duration</div><div class=\"value\">{avg_suite_duration_sec:.2f}s</div></div>
      </div>

      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average Test Duration UI tests Trend</h3>
          <canvas id=\"avg-duration-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Average Test Duration UI tests vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Value</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"speed-avg-ui-duration-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average Test Duration API tests Trend</h3>
          <canvas id=\"avg-api-duration-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Average Test Duration API tests vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Value</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"speed-avg-api-duration-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average UI Test Run Duration Trend</h3>
          <canvas id=\"ui-run-duration-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Average UI Test Run Duration vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Value</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"speed-ui-run-duration-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average API Test Run Duration Trend</h3>
          <canvas id=\"api-run-duration-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Average API Test Run Duration vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Value</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"speed-api-run-duration-rows\"></tbody>
          </table>
        </div>
      </div>
      <div class=\"metric-pair\">
        <div class=\"panel\">
          <h3>Average Pipeline Duration Trend</h3>
          <canvas id=\"ci-pipeline-duration-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Average Pipeline Duration vs Target by Run</h3>
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Value</th>
                <th>Target</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id=\"speed-pipeline-duration-rows\"></tbody>
          </table>
        </div>
      </div>

      <div class=\"panel\">
        <h3>Slowest tests UI</h3>
        <table class=\"slow-tests-table\">
          <thead>
            <tr>
              <th>Run</th>
              <th>Test</th>
              <th>Duration (s)</th>
              <th>Target (s)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id=\"slowest-ui-rows\"></tbody>
        </table>
      </div>
      <div class=\"panel\">
        <h3>Slowest tests API</h3>
        <table class=\"slow-tests-table\">
          <thead>
            <tr>
              <th>Run</th>
              <th>Test</th>
              <th>Duration (s)</th>
              <th>Target (s)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id=\"slowest-api-rows\"></tbody>
        </table>
      </div>
    </section>

  </div>

  <script>
    const data = {points_json};
    const slowestUiTests = {slowest_ui_json};
    const slowestApiTests = {slowest_api_json};
    const passRateTarget = {pass_rate_target:.2f};
    const failRateTarget = {fail_rate_target:.2f};
    const brokenRateTarget = {broken_rate_target:.2f};
    const flakyRateTarget = {flaky_rate_target:.2f};
    const slowUiTargetSec = {slow_ui_target_sec:.2f};
    const slowApiTargetSec = {slow_api_target_sec:.2f};
    const uiRunTargetSec = {ui_run_target_sec:.2f};
    const apiRunTargetSec = {api_run_target_sec:.2f};
    const pipelineTargetSec = {pipeline_target_sec:.2f};

    function setupCanvas(canvas, ctx) {{
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(canvas.clientWidth * dpr));
      canvas.height = Math.max(1, Math.floor(canvas.clientHeight * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }}

    function drawAxis(ctx, w, h, maxY, unit) {{
      const pad = {{ top: 24, right: 18, bottom: 70, left: 54 }};
      const innerW = w - pad.left - pad.right;
      const innerH = h - pad.top - pad.bottom;
      ctx.strokeStyle = '#ddd6ca';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const y = pad.top + (innerH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(w - pad.right, y);
        ctx.stroke();
        const v = (maxY - (maxY / 4) * i).toFixed(2) + unit;
        ctx.fillStyle = '#6d7886';
        ctx.font = '12px sans-serif';
        ctx.fillText(v, 6, y + 4);
      }}
      return {{ pad, innerW, innerH }};
    }}

    function drawLineChart(canvasId, valueKey, maxY, lineColor, pointColor, unit, targetValue = null, targetColor = '#6d7886') {{
      const canvas = document.getElementById(canvasId);
      const ctx = canvas.getContext('2d');
      setupCanvas(canvas, ctx);

      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);

      if (!data.length) {{
        ctx.fillStyle = '#5e6b7a';
        ctx.font = '16px sans-serif';
        ctx.fillText('No data', 20, 40);
        return;
      }}

      const axis = drawAxis(ctx, w, h, Math.max(maxY, 1), unit);
      const pad = axis.pad;
      const innerW = axis.innerW;
      const innerH = axis.innerH;
      const stepX = data.length === 1 ? 0 : innerW / (data.length - 1);

      if (Number.isFinite(targetValue)) {{
        const clampedTarget = Math.max(0, Math.min(targetValue, Math.max(maxY, 1)));
        const targetY = pad.top + innerH - (clampedTarget / Math.max(maxY, 1)) * innerH;
        ctx.save();
        ctx.setLineDash([6, 5]);
        ctx.strokeStyle = targetColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(pad.left, targetY);
        ctx.lineTo(w - pad.right, targetY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = targetColor;
        ctx.font = '12px sans-serif';
        ctx.fillText(`Target: ${{targetValue.toFixed(2)}}${{unit}}`, pad.left + 6, Math.max(14, targetY - 8));
        ctx.restore();
      }}

      const points = data.map((d, i) => {{
        const x = pad.left + i * stepX;
        const y = pad.top + innerH - ((d[valueKey] || 0) / Math.max(maxY, 1)) * innerH;
        return {{ x, y, d }};
      }});

      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 3;
      ctx.beginPath();
      points.forEach((p, i) => {{
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }});
      ctx.stroke();

      points.forEach((p, i) => {{
        ctx.beginPath();
        ctx.fillStyle = pointColor;
        ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
        ctx.fill();
        if (i % Math.max(1, Math.ceil(points.length / 7)) === 0 || i === points.length - 1) {{
          ctx.save();
          ctx.translate(p.x, h - 54);
          ctx.rotate(-0.55);
          ctx.fillStyle = '#5e6b7a';
          ctx.font = '11px sans-serif';
          ctx.fillText(p.d.run_label, 0, 0);
          ctx.restore();
        }}
      }});
    }}

    function drawStabilityChart() {{
      drawLineChart('stability-trend', 'stability_value', 100, '#1f854f', '#159a55', '%');
    }}

    function drawDonutChart(canvasId, valuePercent, color, label) {{
      const canvas = document.getElementById(canvasId);
      const ctx = canvas.getContext('2d');
      setupCanvas(canvas, ctx);

      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);

      const cx = w / 2;
      const cy = h / 2;
      const radius = Math.min(w, h) * 0.30;
      const pct = Math.max(0, Math.min(100, valuePercent));
      const angle = (pct / 100) * Math.PI * 2;
      const green = '#159a55';
      const red = '#cf3f34';
      const remainderColor = color === green ? red : green;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.fillStyle = color;
      ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + angle);
      ctx.closePath();
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.fillStyle = remainderColor;
      ctx.arc(cx, cy, radius, -Math.PI / 2 + angle, -Math.PI / 2 + Math.PI * 2);
      ctx.closePath();
      ctx.fill();

      ctx.beginPath();
      ctx.fillStyle = '#fffdf8';
      ctx.arc(cx, cy, radius * 0.58, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = '#18212f';
      ctx.font = '700 24px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(pct.toFixed(2) + '%', cx, cy + 8);
      ctx.font = '12px sans-serif';
      ctx.fillStyle = '#5e6b7a';
      ctx.fillText(label, cx, cy + 28);
    }}

    function fillTables() {{
      const renderTargetRows = (valueKey, target, unit, higherIsBetter = false) => data.map(d => {{
        const value = d[valueKey] || 0;
        const isOk = higherIsBetter ? value >= target : value <= target;
        const css = isOk ? 'metric-ok' : 'metric-fail';
        const label = isOk ? 'OK' : 'Failed';
        return `
          <tr>
            <td>${{d.run_label}}</td>
            <td>${{value.toFixed(2)}}${{unit}}</td>
            <td>${{higherIsBetter ? '>=' : '<='}} ${{target.toFixed(2)}}${{unit}}</td>
            <td><span class="status-badge ${{css}}">${{label}}</span></td>
          </tr>
        `;
      }}).join('');

      const passDistributionBody = document.getElementById('pass-distribution-rows');
      passDistributionBody.innerHTML = renderTargetRows('pass_percent', passRateTarget, '%', true);

      const failDistributionBody = document.getElementById('fail-distribution-rows');
      failDistributionBody.innerHTML = renderTargetRows('fail_percent', failRateTarget, '%', false);

      const brokenDistributionBody = document.getElementById('broken-distribution-rows');
      brokenDistributionBody.innerHTML = renderTargetRows('broken_percent', brokenRateTarget, '%', false);
      const uiFlakyDistributionBody = document.getElementById('ui-flaky-distribution-rows');
      uiFlakyDistributionBody.innerHTML = renderTargetRows('ui_flaky_percent', flakyRateTarget, '%', false);
      const apiFlakyDistributionBody = document.getElementById('api-flaky-distribution-rows');
      apiFlakyDistributionBody.innerHTML = renderTargetRows('api_flaky_percent', flakyRateTarget, '%', false);

      const speedAvgUiBody = document.getElementById('speed-avg-ui-duration-rows');
      speedAvgUiBody.innerHTML = renderTargetRows('avg_duration_sec', slowUiTargetSec, 's', false);

      const speedAvgApiBody = document.getElementById('speed-avg-api-duration-rows');
      speedAvgApiBody.innerHTML = renderTargetRows('avg_api_duration_sec', slowApiTargetSec, 's', false);

      const speedUiRunBody = document.getElementById('speed-ui-run-duration-rows');
      speedUiRunBody.innerHTML = renderTargetRows('ui_run_duration_sec', uiRunTargetSec, 's', false);

      const speedApiRunBody = document.getElementById('speed-api-run-duration-rows');
      speedApiRunBody.innerHTML = renderTargetRows('api_run_duration_sec', apiRunTargetSec, 's', false);

      const speedPipelineBody = document.getElementById('speed-pipeline-duration-rows');
      speedPipelineBody.innerHTML = renderTargetRows('suite_duration_sec', pipelineTargetSec, 's', false);

      const renderSlowestRows = (rows, targetSec) => {{
        if (!rows.length) {{
          return `
            <tr>
              <td colspan="5">No data</td>
            </tr>
          `;
        }}
        return rows.map(t => `
          <tr>
            <td>${{t.run_label}}</td>
            <td>${{t.test_name}}</td>
            <td>${{t.duration_sec.toFixed(2)}}</td>
            <td>${{targetSec.toFixed(2)}}</td>
            <td><span class="status-badge ${{t.duration_sec <= targetSec ? 'metric-ok' : 'metric-fail'}}">${{t.duration_sec <= targetSec ? 'OK' : 'Failed'}}</span></td>
          </tr>
        `).join('');
      }};

      const slowestUiBody = document.getElementById('slowest-ui-rows');
      slowestUiBody.innerHTML = renderSlowestRows(slowestUiTests, slowUiTargetSec);

      const slowestApiBody = document.getElementById('slowest-api-rows');
      slowestApiBody.innerHTML = renderSlowestRows(slowestApiTests, slowApiTargetSec);
    }}

    function render() {{
      const passRateMax = Math.max(...data.map(d => d.pass_percent), 1);
      const failRateMax = Math.max(...data.map(d => d.fail_percent), 1);
      const brokenRateMax = Math.max(...data.map(d => d.broken_percent), 1);
      const uiFlakyRateMax = Math.max(...data.map(d => d.ui_flaky_percent), 1);
      const apiFlakyRateMax = Math.max(...data.map(d => d.api_flaky_percent), 1);
      const avgDurMax = Math.max(...data.map(d => d.avg_duration_sec), 1);
      const avgApiDurMax = Math.max(...data.map(d => d.avg_api_duration_sec), 1);
      const uiRunDurMax = Math.max(...data.map(d => d.ui_run_duration_sec), 1);
      const apiRunDurMax = Math.max(...data.map(d => d.api_run_duration_sec), 1);
      const suiteDurMax = Math.max(...data.map(d => d.suite_duration_sec), 1);

      drawLineChart('pass-rate-trend', 'pass_percent', passRateMax, '#1b8a4f', '#159a55', '%', {pass_rate_target:.2f}, '#1b8a4f');
      drawLineChart('fail-rate-trend', 'fail_percent', failRateMax, '#b63a31', '#cf3f34', '%', {fail_rate_target:.2f}, '#b63a31');
      drawLineChart('broken-rate-trend', 'broken_percent', brokenRateMax, '#8f3245', '#a73b52', '%', {broken_rate_target:.2f}, '#8f3245');
      drawLineChart('ui-flaky-rate-trend', 'ui_flaky_percent', uiFlakyRateMax, '#1b6f77', '#1f97a3', '%', {flaky_rate_target:.2f}, '#1b6f77');
      drawLineChart('api-flaky-rate-trend', 'api_flaky_percent', apiFlakyRateMax, '#7a5a1a', '#a37b24', '%', {flaky_rate_target:.2f}, '#7a5a1a');
      drawLineChart('avg-duration-trend', 'avg_duration_sec', avgDurMax, '#7a4a18', '#c9762b', 's', {slow_ui_target_sec:.2f}, '#7a4a18');
      drawLineChart('avg-api-duration-trend', 'avg_api_duration_sec', avgApiDurMax, '#1c5d8f', '#2f7fc3', 's', {slow_api_target_sec:.2f}, '#1c5d8f');
      drawLineChart('ui-run-duration-trend', 'ui_run_duration_sec', uiRunDurMax, '#216a4c', '#2c9568', 's', {ui_run_target_sec:.2f}, '#216a4c');
      drawLineChart('api-run-duration-trend', 'api_run_duration_sec', apiRunDurMax, '#6f4b1f', '#a36a28', 's', {api_run_target_sec:.2f}, '#6f4b1f');
      drawLineChart('ci-pipeline-duration-trend', 'suite_duration_sec', suiteDurMax, '#7b2f8e', '#9b4eb2', 's', {pipeline_target_sec:.2f}, '#7b2f8e');
    }}

    fillTables();
    render();
    window.addEventListener('resize', render);
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build HTML dashboard for test quality metrics.")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("downloaded_artifacts"),
        help="Directory containing downloaded .zip artifacts.",
    )
    parser.add_argument(
        "--report-title",
        type=str,
        default="QA Metrics Dashboard",
        help="Main dashboard title.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/metrics_dashboard.html"),
        help="Output HTML file path.",
    )
    parser.add_argument(
        "--gates-config",
        type=Path,
        default=Path("config/metrics/gates.yml"),
        help="YAML config with quality gate thresholds.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.artifacts_dir.exists() or not args.artifacts_dir.is_dir():
        print(f"Artifacts directory not found: {args.artifacts_dir}")
        return 1

    rows = collect_all_stats(args.artifacts_dir)
    gates_config, slowest_tests_limit = load_dashboard_config(args.gates_config)
    slow_records = collect_slowest_tests(args.artifacts_dir, limit=max(1, sum(r.total_tests for r in rows)))
    slowest_tests = [
        {
            "run_name": r.run_name,
            "run_label": fmt_datetime(parse_run_datetime(r.run_name), r.run_name),
            "test_name": r.test_name,
            "duration_sec": round(r.duration_seconds, 2),
            "status": r.status,
        } for r in slow_records
    ]
    slowest_ui_tests = [item for item in slowest_tests if ".ui." in item["test_name"]][:slowest_tests_limit]
    slowest_api_tests = [item for item in slowest_tests if ".api." in item["test_name"]][:slowest_tests_limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        build_html(args.report_title, rows, slowest_ui_tests, slowest_api_tests, gates_config),
        encoding="utf-8",
    )
    print(f"Dashboard generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
