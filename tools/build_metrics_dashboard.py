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
            "name": "Average Test Duration",
            "unit": "s",
            "good_threshold": 8.0,
            "warn_threshold": 12.0,
            "higher_is_better": False,
            "recommendation": "Optimize slow tests and reduce external dependencies.",
        },
    "suite_duration_sec":
        {
            "name": "CI Pipeline Duration (proxy)",
            "unit": "s",
            "good_threshold": 1800.0,
            "warn_threshold": 2700.0,
            "higher_is_better": False,
            "recommendation": "Increase parallelism and remove long serial bottlenecks.",
        },
}
DEFAULT_SLOWEST_TESTS_LIMIT = 4


def load_dashboard_config(config_path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    gates = copy.deepcopy(DEFAULT_GATES)
    slowest_tests_limit = DEFAULT_SLOWEST_TESTS_LIMIT
    if not config_path.exists():
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
    if higher_is_better:
        if value >= good_threshold:
            return "ok"
        if value >= warn_threshold:
            return "warn"
        return "fail"
    if value <= good_threshold:
        return "ok"
    if value <= warn_threshold:
        return "warn"
    return "fail"


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
    status_label = {"ok": "OK", "warn": "Warning", "fail": "Failed"}[status]
    css_class = {"ok": "metric-ok", "warn": "metric-warn", "fail": "metric-fail"}[status]
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
    slowest_tests: list[dict],
    gates_config: dict[str, dict[str, Any]],
) -> str:
    sorted_rows = sorted(rows, key=lambda r: parse_run_datetime(r.run_name) or datetime.min)

    points: list[dict] = []
    for row in sorted_rows:
        run_dt = parse_run_datetime(row.run_name)
        run_success = row.total_tests > 0 and row.passed_tests == row.total_tests
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
                "run_success": run_success,
                "stability_value": 100.0 if run_success else 0.0,
                "total_duration_ms": row.total_duration_ms,
                "avg_duration_sec": round(row.avg_duration_seconds, 2),
                "suite_duration_ms": row.suite_duration_ms,
                "suite_duration_sec": round(row.suite_duration_seconds, 2),
            }
        )

    total_runs = len(rows)
    total_tests = sum(r.total_tests for r in rows)
    total_passed = sum(r.passed_tests for r in rows)
    total_failed = sum(r.failed_tests for r in rows)
    total_broken = sum(r.broken_tests for r in rows)
    total_flaky = sum(r.flaky_tests for r in rows)
    total_duration_ms = sum(r.total_duration_ms for r in rows)
    total_suite_duration_ms = sum(r.suite_duration_ms for r in rows)
    successful_runs = sum(1 for r in rows if r.total_tests > 0 and r.passed_tests == r.total_tests)

    pass_rate = round((total_passed / total_tests * 100.0), 2) if total_tests else 0.0
    fail_rate = round((total_failed / total_tests * 100.0), 2) if total_tests else 0.0
    broken_rate = round((total_broken / total_tests * 100.0), 2) if total_tests else 0.0
    flaky_rate = round((total_flaky / total_tests * 100.0), 2) if total_tests else 0.0
    stability_rate = round((successful_runs / total_runs * 100.0), 2) if total_runs else 0.0

    avg_duration_sec = round((total_duration_ms / total_tests / 1000.0), 2) if total_tests else 0.0
    avg_suite_duration_sec = round((total_suite_duration_ms / total_runs / 1000.0), 2) if total_runs else 0.0

    formulas = {
        "pass_rate":
            f"{total_passed}/{total_tests}={pass_rate:.2f}%" if total_tests else "0/0=0.00%",
        "fail_rate":
            f"{total_failed}/{total_tests}={fail_rate:.2f}%" if total_tests else "0/0=0.00%",
        "broken_rate":
            f"{total_broken}/{total_tests}={broken_rate:.2f}%" if total_tests else "0/0=0.00%",
        "flaky_rate":
            f"{total_flaky}/{total_tests}={flaky_rate:.2f}%" if total_tests else "0/0=0.00%",
        "stability_rate":
            f"{successful_runs}/{total_runs}={stability_rate:.2f}%" if total_runs else "0/0=0.00%",
        "avg_duration_sec":
            (
                f"{round(total_duration_ms / 1000.0, 2)}/{total_tests}={avg_duration_sec:.2f}s"
                if total_tests else "0/0=0.00s"
            ),
        "suite_duration_sec":
            (
                f"{round(total_suite_duration_ms / 1000.0, 2)}/{total_runs}={avg_suite_duration_sec:.2f}s"
                if total_runs else "0/0=0.00s"
            ),
    }
    values = {
        "pass_rate": pass_rate,
        "fail_rate": fail_rate,
        "broken_rate": broken_rate,
        "flaky_rate": flaky_rate,
        "stability_rate": stability_rate,
        "avg_duration_sec": avg_duration_sec,
        "suite_duration_sec": avg_suite_duration_sec,
    }
    gates = []
    for key in DEFAULT_GATES.keys():
        cfg = gates_config.get(key, DEFAULT_GATES[key])
        gates.append(
            build_gate(
                key=key,
                name=str(cfg["name"]),
                value=float(values[key]),
                unit=str(cfg["unit"]),
                good_threshold=float(cfg["good_threshold"]),
                warn_threshold=float(cfg["warn_threshold"]),
                higher_is_better=bool(cfg["higher_is_better"]),
                formula=formulas[key],
                recommendation=str(cfg["recommendation"]),
            )
        )
    gate_by_key = {item["key"]: item for item in gates}
    gates_ok = sum(1 for item in gates if item["status"] == "ok")
    gates_warn = sum(1 for item in gates if item["status"] == "warn")
    gates_fail = sum(1 for item in gates if item["status"] == "fail")
    gate_rows_html = "\n".join(
        (
            "<tr>"
            f"<td>{item['name']}</td>"
            f"<td>{item['value']:.2f}{item['unit']}</td>"
            f"<td>{item['threshold']}</td>"
            f"<td><span class=\"status-badge {item['css_class']}\">{item['status_label']}</span></td>"
            f"<td>{item['formula']}</td>"
            f"<td>{item['recommendation']}</td>"
            "</tr>"
        ) for item in gates
    )

    pass_rate_class = gate_by_key["pass_rate"]["css_class"]
    fail_rate_class = gate_by_key["fail_rate"]["css_class"]
    broken_rate_class = gate_by_key["broken_rate"]["css_class"]
    flaky_rate_class = gate_by_key["flaky_rate"]["css_class"]
    stability_rate_class = gate_by_key["stability_rate"]["css_class"]
    avg_duration_class = gate_by_key["avg_duration_sec"]["css_class"]
    suite_duration_class = gate_by_key["suite_duration_sec"]["css_class"]

    points_json = json.dumps(points, ensure_ascii=False)
    slowest_json = json.dumps(slowest_tests, ensure_ascii=False)
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
    .metric-warn {{ border-color: #b6801e; background: #fff8e8; }}
    .metric-fail {{ border-color: #b43737; background: #fff1f1; }}
    .status-badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-weight: 700;
    }}
    .status-badge.metric-ok {{ color: #0d6e42; }}
    .status-badge.metric-warn {{ color: #7a580e; }}
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
    .chart-single {{ margin-top: 16px; }}

    canvas {{ width: 100%; height: 340px; display: block; }}
    .legend {{ display: flex; gap: 12px; margin-top: 8px; color: #4a5665; font-size: 13px; }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; transform: translateY(1px); }}

    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: #fff; border-radius: 12px; overflow: hidden; font-size: 14px; }}
    th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid #eee9df; }}
    th {{ background: #f9f6f0; font-weight: 600; color: #3f4a57; }}
    tr:hover td {{ background: #fffbf4; }}

    @media (max-width: 960px) {{ .charts-2 {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1 class=\"title\">{report_title_safe}</h1>
    <p class=\"subtitle\">Quality metrics across GitHub runs (Allure artifacts)</p>

    <div class=\"summary\">
      <div class=\"card\"><div class=\"label\">Total Runs</div><div class=\"value\">{total_runs}</div></div>
      <div class=\"card\"><div class=\"label\">Total Tests</div><div class=\"value\">{total_tests}</div></div>
      <div class=\"card\"><div class=\"label\">Generated Metric Groups</div><div class=\"value\">3</div></div>
    </div>

    <section class=\"group\">
      <h2>🚦 Quality Gates Overview</h2>
      <p class=\"desc\">Each metric is checked against a threshold. Failed gates are highlighted in red and need action.</p>
      <div class=\"metric-cards\">
        <div class=\"card metric-ok\"><div class=\"label\">OK Gates</div><div class=\"value\">{gates_ok}</div></div>
        <div class=\"card metric-warn\"><div class=\"label\">Warning Gates</div><div class=\"value\">{gates_warn}</div></div>
        <div class=\"card metric-fail\"><div class=\"label\">Failed Gates</div><div class=\"value\">{gates_fail}</div></div>
      </div>
      <div class=\"panel\">
        <h3>Gate Status by Metric</h3>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Current Value</th>
              <th>Target</th>
              <th>Status</th>
              <th>Calculation</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {gate_rows_html}
          </tbody>
        </table>
      </div>
    </section>

    <section class=\"group\">
      <h2>1️⃣ Test Result Distribution</h2>
      <p class=\"desc\">Distribution of test outcomes by status.</p>
      <div class=\"metric-cards\">
        <div class=\"card {pass_rate_class}\"><div class=\"label\">pass rate</div><div class=\"value\">{pass_rate:.2f}%</div></div>
        <div class=\"card {fail_rate_class}\"><div class=\"label\">fail rate</div><div class=\"value\">{fail_rate:.2f}%</div></div>
        <div class=\"card {broken_rate_class}\"><div class=\"label\">broken rate</div><div class=\"value\">{broken_rate:.2f}%</div></div>
      </div>

      <div class=\"panel\">
        <h3>How Metrics Are Calculated</h3>
        <div class=\"formulas\">
          pass rate = passed tests / total tests = {total_passed} / {total_tests} = {pass_rate:.2f}%<br/>
          fail rate = failed tests / total tests = {total_failed} / {total_tests} = {fail_rate:.2f}%<br/>
          broken rate = broken tests / total tests = {total_broken} / {total_tests} = {broken_rate:.2f}%
        </div>
      </div>

      <div class=\"charts-2\">
        <div class=\"panel\">
          <h3>Pass Rate</h3>
          <canvas id=\"pass-rate-donut\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Fail Rate</h3>
          <canvas id=\"fail-rate-donut\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Broken Rate</h3>
          <canvas id=\"broken-rate-donut\"></canvas>
        </div>
      </div>

      <div class=\"panel\">
        <h3>Distribution by Run</h3>
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Passed</th>
              <th>Failed</th>
              <th>Broken</th>
              <th>Pass %</th>
              <th>Fail %</th>
              <th>Broken %</th>
            </tr>
          </thead>
          <tbody id=\"distribution-rows\"></tbody>
        </table>
      </div>
    </section>

    <section class=\"group\">
      <h2>2️⃣ Test Stability Metrics</h2>
      <p class=\"desc\">Show how reliable your tests are over time.</p>
      <div class=\"formulas\">
        Pass Rate = Passed tests / Total tests<br/>
        Flaky Rate = Flaky tests / Total tests<br/>
        Test Stability = Successful runs / Total runs
      </div>
      <div class=\"metric-cards\">
        <div class=\"card {pass_rate_class}\"><div class=\"label\">Pass Rate</div><div class=\"value\">{pass_rate:.2f}%</div></div>
        <div class=\"card {flaky_rate_class}\"><div class=\"label\">Flaky Rate</div><div class=\"value\">{flaky_rate:.2f}%</div></div>
        <div class=\"card {stability_rate_class}\"><div class=\"label\">Test Stability</div><div class=\"value\">{stability_rate:.2f}%</div></div>
        <div class=\"card\"><div class=\"label\">Successful Runs</div><div class=\"value\">{successful_runs}/{total_runs}</div></div>
      </div>

      <div class=\"charts-2\">
        <div class=\"panel\">
          <h3>Pass Rate Trend</h3>
          <canvas id=\"pass-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Flaky Rate Trend</h3>
          <canvas id=\"flaky-trend\"></canvas>
        </div>
      </div>

      <div class=\"panel chart-single\">
        <h3>Test Stability by Run</h3>
        <canvas id=\"stability-trend\"></canvas>
        <div class=\"legend\">
          <span><span class=\"dot\" style=\"background:#159a55;\"></span>Successful run (100%)</span>
          <span><span class=\"dot\" style=\"background:#d14f45;\"></span>Unstable run (0%)</span>
        </div>
      </div>

      <div class=\"panel\">
        <h3>Stability by Run</h3>
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Total tests</th>
              <th>Pass %</th>
              <th>Flaky %</th>
              <th>Successful run</th>
            </tr>
          </thead>
          <tbody id=\"stability-rows\"></tbody>
        </table>
      </div>
    </section>

    <section class=\"group\">
      <h2>3️⃣ Speed Metrics</h2>
      <p class=\"desc\">Show how fast the pipeline is. CI Pipeline Duration is currently estimated from available test runtime data.</p>
      <div class=\"formulas\">
        Test Execution Time = Total runtime<br/>
        Average Test Duration = Total runtime / Number of tests<br/>
        CI Pipeline Duration = build + deploy + tests
      </div>
      <div class=\"metric-cards\">
        <div class=\"card\"><div class=\"label\">Test Execution Time</div><div class=\"value\">{round(total_suite_duration_ms / 1000.0, 1)}s</div></div>
        <div class=\"card {avg_duration_class}\"><div class=\"label\">Average Test Duration</div><div class=\"value\">{avg_duration_sec:.2f}s</div></div>
        <div class=\"card {suite_duration_class}\"><div class=\"label\">CI Pipeline Duration</div><div class=\"value\">{avg_suite_duration_sec:.2f}s</div></div>
      </div>

      <div class=\"charts-2\">
        <div class=\"panel\">
          <h3>Average Test Duration Trend</h3>
          <canvas id=\"avg-duration-trend\"></canvas>
        </div>
        <div class=\"panel\">
          <h3>Suite Duration Trend</h3>
          <canvas id=\"suite-duration-trend\"></canvas>
        </div>
      </div>

      <div class=\"panel\">
        <h3>Execution Time by Run</h3>
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Avg test duration (s)</th>
              <th>Suite duration (s)</th>
            </tr>
          </thead>
          <tbody id=\"duration-rows\"></tbody>
        </table>
      </div>

      <div class=\"panel\">
        <h3>Slowest tests</h3>
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Test</th>
              <th>Duration (s)</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id=\"slowest-rows\"></tbody>
        </table>
      </div>
    </section>

  </div>

  <script>
    const data = {points_json};
    const slowestTests = {slowest_json};

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

    function drawLineChart(canvasId, valueKey, maxY, lineColor, pointColor, unit) {{
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
      const stabilityBody = document.getElementById('stability-rows');
      stabilityBody.innerHTML = data.map(d => `
        <tr>
          <td>${{d.run_label}}</td>
          <td>${{d.total_tests}}</td>
          <td>${{d.pass_percent.toFixed(2)}}%</td>
          <td>${{d.flaky_percent.toFixed(2)}}%</td>
          <td>${{d.run_success ? 'Yes' : 'No'}}</td>
        </tr>
      `).join('');

      const durationBody = document.getElementById('duration-rows');
      durationBody.innerHTML = data.map(d => `
        <tr>
          <td>${{d.run_label}}</td>
          <td>${{d.avg_duration_sec.toFixed(2)}}</td>
          <td>${{d.suite_duration_sec.toFixed(2)}}</td>
        </tr>
      `).join('');

      const distributionBody = document.getElementById('distribution-rows');
      distributionBody.innerHTML = data.map(d => `
        <tr>
          <td>${{d.run_label}}</td>
          <td>${{d.passed_tests}}</td>
          <td>${{d.failed_tests}}</td>
          <td>${{d.broken_tests}}</td>
          <td>${{d.pass_percent.toFixed(2)}}%</td>
          <td>${{d.fail_percent.toFixed(2)}}%</td>
          <td>${{d.broken_percent.toFixed(2)}}%</td>
        </tr>
      `).join('');

      const slowestBody = document.getElementById('slowest-rows');
      slowestBody.innerHTML = slowestTests.map(t => `
        <tr>
          <td>${{t.run_label}}</td>
          <td>${{t.test_name}}</td>
          <td>${{t.duration_sec.toFixed(2)}}</td>
          <td>${{t.status}}</td>
        </tr>
      `).join('');
    }}

    function render() {{
      const passMax = Math.max(...data.map(d => d.pass_percent), 1);
      const flakyMax = Math.max(...data.map(d => d.flaky_percent), 1);
      const avgDurMax = Math.max(...data.map(d => d.avg_duration_sec), 1);
      const suiteDurMax = Math.max(...data.map(d => d.suite_duration_sec), 1);

      drawLineChart('pass-trend', 'pass_percent', passMax, '#2f6bff', '#2f6bff', '%');
      drawLineChart('flaky-trend', 'flaky_percent', flakyMax, '#0a7a78', '#ff7f50', '%');
      drawStabilityChart();
      drawDonutChart('pass-rate-donut', {pass_rate:.2f}, '#159a55', 'pass rate');
      drawDonutChart('fail-rate-donut', {fail_rate:.2f}, '#cf3f34', 'fail rate');
      drawDonutChart('broken-rate-donut', {broken_rate:.2f}, '#cf3f34', 'broken rate');
      drawLineChart('avg-duration-trend', 'avg_duration_sec', avgDurMax, '#7a4a18', '#c9762b', 's');
      drawLineChart('suite-duration-trend', 'suite_duration_sec', suiteDurMax, '#7b2f8e', '#9b4eb2', 's');
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
        default=Path("metrics_gates.yml"),
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
    slow_records = collect_slowest_tests(args.artifacts_dir, limit=slowest_tests_limit)
    slowest_tests = [
        {
            "run_name": r.run_name,
            "run_label": fmt_datetime(parse_run_datetime(r.run_name), r.run_name),
            "test_name": r.test_name,
            "duration_sec": round(r.duration_seconds, 2),
            "status": r.status,
        } for r in slow_records
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_html(args.report_title, rows, slowest_tests, gates_config), encoding="utf-8")
    print(f"Dashboard generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
