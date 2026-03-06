# pipe_team_open_msr_auto

## Allure is required

For correct test execution and report generation, install **Allure CLI** before running tests.

### macOS

Install with Homebrew:

```bash
brew install allure
```

Check installation:

```bash
allure --version
```

### Windows

Install with Chocolatey:

```powershell
choco install allure-commandline
```

or with Scoop:

```powershell
scoop install allure
```

Check installation:

```powershell
allure --version
```

## How to run tests in parallel

```pytest --seed 123 -n 2```
where [n] is number of workers

## How to run UI autotests
Need to install browsers for Playwright:  
```bash
playwright install```

## How to generate Allure report locally

Run tests and save Allure results:

```bash
pytest --alluredir=allure-results
```

Open report in browser:

```bash
allure serve allure-results
```

Alternative (generate static report folder):

```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```
