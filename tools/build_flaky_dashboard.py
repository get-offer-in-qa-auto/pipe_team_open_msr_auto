from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from allure_flaky_stats import RunStats, collect_all_stats, collect_slowest_tests


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


def build_html(report_title: str, rows: list[RunStats], slowest_tests: list[dict]) -> str:
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

    points_json = json.dumps(points, ensure_ascii=False)
    slowest_json = json.dumps(slowest_tests, ensure_ascii=False)
    report_title_safe = report_title.replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!doctype html>
<html lang=\"ru\">
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
      <h2>1️⃣ Test Result Distribution</h2>
      <p class=\"desc\">Распределение результатов тестов по статусам.</p>
      <div class=\"metric-cards\">
        <div class=\"card\"><div class=\"label\">pass rate</div><div class=\"value\">{pass_rate:.2f}%</div></div>
        <div class=\"card\"><div class=\"label\">fail rate</div><div class=\"value\">{fail_rate:.2f}%</div></div>
        <div class=\"card\"><div class=\"label\">broken rate</div><div class=\"value\">{broken_rate:.2f}%</div></div>
      </div>

      <div class=\"panel chart-single\">
        <h3>Distribution Trend by Run</h3>
        <canvas id=\"distribution-trend\"></canvas>
      </div>

      <div class=\"panel\">
        <h3>Distribution by Run</h3>
        <table>
          <thead>
            <tr>
              <th>Run</th>
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
      <h2>2️⃣ Метрики стабильности тестов</h2>
      <p class=\"desc\">Показывают, насколько тестам можно доверять.</p>
      <div class=\"formulas\">
        Pass Rate = Passed tests / Total tests<br/>
        Flaky Rate = Flaky tests / Total tests<br/>
        Test Stability = Successful runs / Total runs
      </div>
      <div class=\"metric-cards\">
        <div class=\"card\"><div class=\"label\">Pass Rate</div><div class=\"value\">{pass_rate:.2f}%</div></div>
        <div class=\"card\"><div class=\"label\">Flaky Rate</div><div class=\"value\">{flaky_rate:.2f}%</div></div>
        <div class=\"card\"><div class=\"label\">Test Stability</div><div class=\"value\">{stability_rate:.2f}%</div></div>
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
        <h3>Стабильность по запускам</h3>
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
      <h2>3️⃣ Метрики скорости</h2>
      <p class=\"desc\">Показывают, насколько быстрый pipeline. CI Pipeline Duration сейчас оценивается по доступным runtime данным тестов.</p>
      <div class=\"formulas\">
        Test Execution Time = Total runtime<br/>
        Average Test Duration = Total runtime / Number of tests<br/>
        CI Pipeline Duration = build + deploy + tests
      </div>
      <div class=\"metric-cards\">
        <div class=\"card\"><div class=\"label\">Test Execution Time</div><div class=\"value\">{round(total_suite_duration_ms / 1000.0, 1)}s</div></div>
        <div class=\"card\"><div class=\"label\">Average Test Duration</div><div class=\"value\">{avg_duration_sec:.2f}s</div></div>
        <div class=\"card\"><div class=\"label\">CI Pipeline Duration</div><div class=\"value\">{avg_suite_duration_sec:.2f}s</div></div>
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
        <h3>Время выполнения по запускам</h3>
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

    function drawDistributionChart() {{
      const canvas = document.getElementById('distribution-trend');
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

      const axis = drawAxis(ctx, w, h, 100, '%');
      const pad = axis.pad;
      const innerW = axis.innerW;
      const innerH = axis.innerH;
      const stepX = data.length === 1 ? 0 : innerW / (data.length - 1);

      function lineFor(key, stroke, fill) {{
        const points = data.map((d, i) => {{
          const x = pad.left + i * stepX;
          const y = pad.top + innerH - ((d[key] || 0) / 100) * innerH;
          return {{ x, y, d }};
        }});
        ctx.strokeStyle = stroke;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        points.forEach((p, i) => {{
          if (i === 0) ctx.moveTo(p.x, p.y);
          else ctx.lineTo(p.x, p.y);
        }});
        ctx.stroke();
        points.forEach((p, i) => {{
          ctx.beginPath();
          ctx.fillStyle = fill;
          ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
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

      lineFor('pass_percent', '#2f6bff', '#2f6bff');
      lineFor('fail_percent', '#cf3f34', '#cf3f34');
      lineFor('broken_percent', '#6e42c1', '#6e42c1');
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
      drawDistributionChart();
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.artifacts_dir.exists() or not args.artifacts_dir.is_dir():
        print(f"Artifacts directory not found: {args.artifacts_dir}")
        return 1

    rows = collect_all_stats(args.artifacts_dir)
    slow_records = collect_slowest_tests(args.artifacts_dir, limit=20)
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
    args.output.write_text(build_html(args.report_title, rows, slowest_tests), encoding="utf-8")
    print(f"Dashboard generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
