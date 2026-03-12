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
```

Run:

```bash
python3 tools/github_artifacts_ui.py
```

Fields in UI:
- `GitHub Token` - loaded from `.env` (`GITHUB_TOKEN`) if present; can be edited manually in the UI
- `Owner` - GitHub org/user name
- `Repo` - repository name
- `Branch` - required branch to filter (for example: `main`, `develop`, `release`)
- `Days back` - how many days back to search
- `Output folder` - where `.zip` artifacts will be downloaded

Main actions in UI:
- `Find artifacts` - only list artifacts
- `Find + download` - download all non-expired artifacts
- `Download only allure-results` - download only non-expired artifacts with `allure-results` in the name
- `Generate report` - download `allure-results`, generate `reports/metrics_dashboard.html`, and open it in browser

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
python3 tools/build_flaky_dashboard.py \
  --artifacts-dir downloaded_artifacts \
  --report-title "QA Metrics Dashboard (main)" \
  --output reports/metrics_dashboard.html
```
