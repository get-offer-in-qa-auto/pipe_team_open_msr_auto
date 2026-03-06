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
