# pipe_team_open_msr_auto

UI/API autotests with `pytest`, `playwright`, and `allure`.

## 1. Prerequisites

### Python dependencies

```bash
python3 -m pip install -r requirements.txt
```

### Allure CLI (required for reports)

macOS:

```bash
brew install allure
allure --version
```

Windows (Chocolatey):

```powershell
choco install allure-commandline
allure --version
```

Windows (Scoop):

```powershell
scoop install allure
allure --version
```

## 2. Pre-commit checks

Project uses these checks before commit:
- remove unused imports (`ruff --fix --select F401`)
- `ruff`
- `isort`
- `yapf` (style: `facebook`, column limit: `120`)

Install git hooks:

```bash
pre-commit install
```

Run all checks manually:

```bash
pre-commit run --all-files
```

## 3. Run tests

Default run:

```bash
pytest
```

Run in parallel (`-n` = number of workers):

```bash
pytest --seed 123 -n 2
```

## 4. UI tests (Playwright)

Install browsers once:

```bash
playwright install
```

Run UI tests:

```bash
pytest tests/ui
```

## 5. Allure report

Run tests and save results:

```bash
pytest --alluredir=allure-results
```

Open interactive local report:

```bash
allure serve allure-results
```

Generate static report:

```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```

## 6. CI report artifact (no external hosting)

GitHub Actions saves generated HTML report on page https://get-offer-in-qa-auto.github.io/pipe_team_open_msr_auto

## 7. GitHub artifacts UI collector

Local desktop UI for collecting GitHub Actions artifacts from selected branch for the last N days.

Create `.env` in project root:

```bash
GITHUB_TOKEN=your_personal_access_token
REPORT_EMAIL_TO=qa-team@example.com,dev-team@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=bot@example.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=bot@example.com
SMTP_USE_SSL=false
```

Run:

```bash
python3 tools/github_artifacts_ui.py
```

Fields in UI:
- `GitHub Token` - loaded from `.env` (`GITHUB_TOKEN`) if present; can be edited manually in the UI
- `Owner` - GitHub org/user name
- `Repo` - repository name
- `Branch` - required branch to filter (default from `config/metrics/runtime.yml` -> `source.branch`)
- `Days back` - how many days back to search (default from `config/metrics/runtime.yml` -> `source.days_back`)
- `Output folder` - where `.zip` artifacts will be downloaded

Main actions in UI:
- `Generate report` - download `allure-results`, generate `reports/metrics_dashboard.html`, and open it in browser
- `Send report` - send already generated `reports/metrics_dashboard.html` to recipients via SMTP

Email recipients field:
- default value is loaded from `config/metrics/delivery.yml` -> `email.recipients`
- if `REPORT_EMAIL_TO` is set in `.env`, it overrides config recipients in UI
- you can remove it and add one or more recipients separated by commas

If report sending fails:
- UI now shows detailed error diagnostics for missing SMTP variables and report generation issues.
- Check `.env` contains:
  - `SMTP_HOST=smtp.gmail.com`
  - `SMTP_PORT=465`
  - `SMTP_USERNAME=tuzikthecoolest@gmail.com`
  - `SMTP_PASSWORD=YOUR_GMAIL_APP_PASSWORD`
  - `SMTP_FROM=tuzikthecoolest@gmail.com`
  - `SMTP_USE_SSL=true`
- For Gmail, use an app password (regular account password will fail with `Application-specific password required`).

## 8. Flaky tests stats from downloaded artifacts

After downloading Allure artifacts (`.zip`) to `downloaded_artifacts`, run:

```bash
python3 tools/allure_flaky_stats.py --artifacts-dir downloaded_artifacts
```

Output format:
- `run,total_tests,passed_tests,pass_percent,failed_tests,fail_percent,broken_tests,broken_percent,flaky_tests,flaky_percent,total_duration_ms,avg_duration_sec,suite_duration_ms,suite_duration_sec`
- `TOTAL,...` summary across all runs

## 9. Web dashboard for grouped quality metrics

Generate a static HTML page with metric title, KPI cards, trend chart, and runs table:

```bash
python3 tools/build_metrics_dashboard.py \
  --artifacts-dir downloaded_artifacts \
  --report-title "QA Metrics Dashboard (main)" \
  --output reports/metrics_dashboard.html
```

Quality gates configuration:
- thresholds/recommendations are stored in `config/metrics/gates.yml`
- report settings are also in `config/metrics/gates.yml` (for example `report.slowest_tests_limit`)
- default path is loaded automatically
- you can pass custom config path:

```bash
python3 tools/build_metrics_dashboard.py --gates-config ./config/metrics/gates.yml
```

Metrics config structure:
- `config/metrics/gates.yml` - quality gates and report metric settings
- `config/metrics/runtime.yml` - default data source settings (`source.branch`, `source.days_back`)
- `config/metrics/delivery.yml` - report recipients (`email.recipients`)

## 10. Automatic metrics report in GitHub Actions

Workflow supports metrics report generation and email delivery with a flag.

How to enable:
- For manual run (`workflow_dispatch`): set input `send_metrics_report=true`
- For push/PR runs: set repository variable `METRICS_REPORT_ENABLED=true`

Email recipients list:
- Set in `config/metrics/delivery.yml`:
- `email.recipients: ["ekaterina-konchina@yandex.ru", "other@example.com"]`
- Workflow job `metrics-email-report` reads recipients from this config automatically

Published links:
- Allure report: `https://<owner>.github.io/<repo>/index.html`
- Metrics report: `https://<owner>.github.io/<repo>/metrics/index.html`

Pipeline artifacts:
- `allure-html-report`
- `metrics-dashboard-html`

Required repository secrets:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
