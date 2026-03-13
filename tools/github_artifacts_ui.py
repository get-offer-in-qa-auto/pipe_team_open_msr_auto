from __future__ import annotations

import mimetypes
import os
import re
import smtplib
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import requests
import yaml

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30
DEFAULT_REPORT_RECIPIENTS = ["ekaterina-konchina@yandex.ru"]
DEFAULT_BRANCH = "main"
DEFAULT_DAYS_BACK = 10
DELIVERY_CONFIG_PATH = Path("config/metrics/delivery.yml")
RUNTIME_CONFIG_PATH = Path("config/metrics/runtime.yml")


def load_env_value(key: str, env_path: Path | None = None) -> str:
    file_path = env_path or (Path.cwd() / ".env")
    if not file_path.exists():
        return ""

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            continue

        found_key, value = line.split("=", 1)
        if found_key.strip() != key:
            continue

        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        return value

    return ""


def config_value(key: str, default: str = "") -> str:
    return load_env_value(key) or os.getenv(key, default)


def default_recipients_from_config(config_path: Path | None = None) -> str:
    path = config_path or (Path.cwd() / DELIVERY_CONFIG_PATH)
    if not path.exists():
        legacy_path = Path.cwd() / "report_delivery.yml"
        if legacy_path.exists():
            path = legacy_path
        else:
            return ",".join(DEFAULT_REPORT_RECIPIENTS)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return ",".join(DEFAULT_REPORT_RECIPIENTS)

    email_cfg = payload.get("email")
    if not isinstance(email_cfg, dict):
        return ",".join(DEFAULT_REPORT_RECIPIENTS)

    recipients = email_cfg.get("recipients")
    if isinstance(recipients, list):
        parsed = [str(item).strip() for item in recipients if str(item).strip()]
        if parsed:
            return ",".join(parsed)
    return ",".join(DEFAULT_REPORT_RECIPIENTS)


def runtime_defaults_from_config(config_path: Path | None = None) -> tuple[str, str]:
    path = config_path or (Path.cwd() / RUNTIME_CONFIG_PATH)
    if not path.exists():
        return DEFAULT_BRANCH, str(DEFAULT_DAYS_BACK)
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return DEFAULT_BRANCH, str(DEFAULT_DAYS_BACK)

    source_cfg = payload.get("source")
    if not isinstance(source_cfg, dict):
        return DEFAULT_BRANCH, str(DEFAULT_DAYS_BACK)

    branch = str(source_cfg.get("branch", DEFAULT_BRANCH)).strip() or DEFAULT_BRANCH
    days_raw = source_cfg.get("days_back", DEFAULT_DAYS_BACK)
    try:
        days = int(days_raw)
    except (TypeError, ValueError):
        days = DEFAULT_DAYS_BACK
    if days < 0:
        days = DEFAULT_DAYS_BACK
    return branch, str(days)


def log_info(message: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [report-ui] {message}")


@dataclass
class Artifact:
    artifact_id: int
    name: str
    branch: str
    created_at: datetime
    expired: bool
    download_url: str


class GithubArtifactsClient:
    def __init__(self, token: str, owner: str, repo: str) -> None:
        self.owner = owner.strip()
        self.repo = repo.strip()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token.strip()}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "github-artifacts-ui"
            }
        )

    def list_artifacts(self, branch: str, days: int) -> list[Artifact]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        found: list[Artifact] = []
        page = 1

        while True:
            url = f"{GITHUB_API}/repos/{self.owner}/{self.repo}/actions/artifacts"
            resp = self.session.get(url, params={"per_page": 100, "page": page}, timeout=DEFAULT_TIMEOUT)

            if resp.status_code >= 400:
                raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")

            payload: dict[str, Any] = resp.json()
            items = payload.get("artifacts", [])
            if not items:
                break

            for item in items:
                workflow_run = item.get("workflow_run") or {}
                head_branch = workflow_run.get("head_branch") or ""

                created_raw = item.get("created_at")
                if not created_raw:
                    continue

                created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                if created_at < since:
                    continue
                if head_branch != branch:
                    continue

                found.append(
                    Artifact(
                        artifact_id=item["id"],
                        name=item["name"],
                        branch=head_branch,
                        created_at=created_at,
                        expired=bool(item.get("expired", False)),
                        download_url=item["archive_download_url"],
                    )
                )

            page += 1

        return sorted(found, key=lambda a: a.created_at, reverse=True)

    def download_artifact(self, artifact: Artifact, output_dir: Path, progress_cb: Any | None = None) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{artifact.created_at.strftime('%Y%m%d_%H%M%S')}_{artifact.artifact_id}_{artifact.name}.zip"
        sanitized_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in filename)
        target = output_dir / sanitized_name

        with self.session.get(artifact.download_url, timeout=DEFAULT_TIMEOUT, stream=True, allow_redirects=True) as r:
            if r.status_code >= 400:
                raise RuntimeError(f"Failed to download artifact {artifact.name}: {r.status_code}")
            total_bytes = int(r.headers.get("Content-Length", "0") or 0)
            received_bytes = 0
            with open(target, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        received_bytes += len(chunk)
                        if progress_cb is not None:
                            progress_cb(received_bytes, total_bytes)

        return target


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GitHub Artifacts Collector")
        self.geometry("900x520")

        token_from_env_file = load_env_value("GITHUB_TOKEN")
        default_owner, default_repo = self._detect_repo_from_git()
        default_branch, default_days = runtime_defaults_from_config()
        self.token_var = tk.StringVar(value=token_from_env_file or os.getenv("GITHUB_TOKEN", ""))
        self.owner_var = tk.StringVar(value=default_owner)
        self.repo_var = tk.StringVar(value=default_repo)
        self.branch_var = tk.StringVar(value=config_value("METRICS_BRANCH", default_branch))
        self.days_var = tk.StringVar(value=config_value("METRICS_DAYS_BACK", default_days))
        self.output_var = tk.StringVar(value=str(Path.cwd() / "downloaded_artifacts"))
        self.email_to_var = tk.StringVar(value=config_value("REPORT_EMAIL_TO", default_recipients_from_config()))

        self._build_ui()
        self._ensure_visible()

    def _build_ui(self) -> None:
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="GitHub Token").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.token_var, show="*",
                  width=80).grid(row=0, column=1, columnspan=3, sticky="ew", padx=8)

        ttk.Label(frm, text="Owner").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.owner_var, width=30).grid(row=1, column=1, sticky="ew", padx=8, pady=(8, 0))

        ttk.Label(frm, text="Repo").grid(row=1, column=2, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.repo_var, width=30).grid(row=1, column=3, sticky="ew", padx=8, pady=(8, 0))

        ttk.Label(frm, text="Branch (required)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.branch_var, width=30).grid(row=2, column=1, sticky="ew", padx=8, pady=(8, 0))

        ttk.Label(frm, text="Days back").grid(row=2, column=2, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.days_var, width=30).grid(row=2, column=3, sticky="ew", padx=8, pady=(8, 0))

        ttk.Label(frm, text="Output folder").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.output_var,
                  width=70).grid(row=3, column=1, columnspan=2, sticky="ew", padx=8, pady=(8, 0))
        ttk.Button(frm, text="Browse", command=self._choose_dir).grid(row=3, column=3, sticky="ew", pady=(8, 0))

        ttk.Label(frm, text="Email recipients").grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.email_to_var,
                  width=70).grid(row=4, column=1, columnspan=3, sticky="ew", padx=8, pady=(8, 0))

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(12, 8))
        self.generate_report_btn = ttk.Button(
            btn_frame,
            text="Generate report",
            command=self._run_generate_report,
        )
        self.generate_report_btn.pack(side=tk.LEFT)
        self.send_report_btn = ttk.Button(
            btn_frame,
            text="Send report",
            command=self._run_send_report,
        )
        self.send_report_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100)
        self.progress.grid(row=6, column=0, columnspan=4, sticky="ew")

        columns = ("id", "name", "branch", "created", "expired")
        self.tree = ttk.Treeview(frm, columns=columns, show="headings", height=14)
        headings = {
            "id": "ID",
            "name": "Name",
            "branch": "Branch",
            "created": "Created (UTC)",
            "expired": "Expired",
        }
        widths = {"id": 90, "name": 260, "branch": 110, "created": 190, "expired": 90}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.grid(row=7, column=0, columnspan=4, sticky="nsew")

        self.status = tk.StringVar(value="Ready")
        ttk.Label(frm, textvariable=self.status).grid(row=8, column=0, columnspan=4, sticky="w", pady=(8, 0))

        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(3, weight=1)
        frm.grid_rowconfigure(7, weight=1)

    def _ensure_visible(self) -> None:
        self.update_idletasks()
        width = self.winfo_width() or 900
        height = self.winfo_height() or 520
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()
        self.state("normal")

        # Re-raise a few times: on macOS windows started from terminal can
        # occasionally open behind other spaces/apps.
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.after(500, self.lift)
        self.after(900, self.lift)
        self.focus_force()

    def _detect_repo_from_git(self) -> tuple[str, str]:
        try:
            remote = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            return "", ""

        # Supports:
        # - git@github.com:owner/repo.git
        # - https://github.com/owner/repo(.git)
        match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", remote)
        if not match:
            return "", ""
        return match.group("owner"), match.group("repo")

    def _detect_branch_from_git(self) -> str:
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            return branch
        except (FileNotFoundError, subprocess.CalledProcessError):
            return ""

    def _choose_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self.output_var.get())
        if path:
            self.output_var.set(path)

    def _validate(self) -> tuple[str, str, str, int, Path]:
        token = self.token_var.get().strip()
        owner = self.owner_var.get().strip()
        repo = self.repo_var.get().strip()
        branch = self.branch_var.get().strip()

        if not token:
            raise ValueError("GitHub token is required")
        if not owner or not repo:
            raise ValueError("Owner and repo are required")
        if not branch:
            raise ValueError("Branch is required")

        try:
            days = int(self.days_var.get().strip())
        except ValueError as e:
            raise ValueError("Days back must be an integer") from e
        if days < 0:
            raise ValueError("Days back must be >= 0")

        output = Path(self.output_var.get().strip())
        return owner, repo, branch, days, output

    def _set_status(self, text: str) -> None:
        self.status.set(text)
        self.update_idletasks()

    def _set_buttons_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.generate_report_btn.configure(state=state)
        self.send_report_btn.configure(state=state)

    def _set_progress_indeterminate(self, active: bool) -> None:
        if active:
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
            return
        self.progress.stop()
        self.progress.configure(mode="determinate", maximum=100, value=0)

    def _set_progress(self, value: int, maximum: int) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", maximum=max(1, maximum), value=max(0, value))
        self.update_idletasks()

    @staticmethod
    def _format_size(value: int) -> str:
        if value < 1024 * 1024:
            return f"{value / 1024:.1f} KB"
        return f"{value / (1024 * 1024):.1f} MB"

    def _clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _insert_artifacts(self, artifacts: list[Artifact]) -> None:
        self._clear_table()
        for artifact in artifacts:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    artifact.artifact_id, artifact.name, artifact.branch, artifact.created_at.isoformat(),
                    artifact.expired
                ),
            )

    def _run_generate_report(self) -> None:
        self._run_worker(download=True, only_allure_results=True, generate_report=True, send_email=False)

    def _run_send_report(self) -> None:
        self._set_buttons_enabled(False)
        self._set_progress_indeterminate(True)

        def work() -> None:
            try:
                branch = self.branch_var.get().strip() or "main"
                report_path = Path.cwd() / "reports" / "metrics_dashboard.html"
                if not report_path.exists():
                    raise ValueError(f"Report not found: {report_path}. Generate report first.")
                self.after(0, lambda: self._set_status("Sending report via email..."))
                self._send_report_email(report_path, branch)
                self.after(0, lambda p=report_path: self._set_status(f"Report emailed: {p}"))
            except Exception as exc:  # noqa: BLE001
                log_info(f"Send report failed: {exc}")
                self.after(0, lambda err=exc: messagebox.showerror("Error", str(err)))
                self.after(0, lambda: self._set_status("Failed"))
            finally:
                self.after(0, lambda: self._set_progress_indeterminate(False))
                self.after(0, lambda: self._set_buttons_enabled(True))

        threading.Thread(target=work, daemon=True).start()

    @staticmethod
    def _parse_recipients(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _required_smtp_keys() -> list[str]:
        return ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"]

    def _validate_smtp_config(self) -> dict[str, str]:
        values = {key: config_value(key).strip() for key in self._required_smtp_keys()}
        missing = [key for key, value in values.items() if not value]
        if missing:
            message = (
                "SMTP settings are incomplete.\n\n"
                "Missing variables:\n"
                f"- {', '.join(missing)}\n\n"
                "Expected .env format:\n"
                "SMTP_HOST=smtp.gmail.com\n"
                "SMTP_PORT=465\n"
                "SMTP_USERNAME=tuzikthecoolest@gmail.com\n"
                "SMTP_PASSWORD=YOUR_GMAIL_APP_PASSWORD\n"
                "SMTP_FROM=tuzikthecoolest@gmail.com\n"
                "SMTP_USE_SSL=true"
            )
            raise ValueError(message)
        return values

    def _generate_dashboard(self, artifacts_dir: Path, branch: str) -> Path:
        script_path = Path(__file__).with_name("build_metrics_dashboard.py")
        report_path = Path.cwd() / "reports" / "metrics_dashboard.html"
        log_info(f"Generate dashboard: branch='{branch}', artifacts_dir='{artifacts_dir}'")
        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--artifacts-dir",
                str(artifacts_dir),
                "--report-title",
                f"QA Metrics Dashboard ({branch})",
                "--output",
                str(report_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            details = stderr or stdout or "Unknown error"
            raise RuntimeError(
                "Failed to generate dashboard.\n\n"
                "Details:\n"
                f"{details}\n\n"
                "Hint: check that downloaded artifacts exist and build_metrics_dashboard.py runs locally."
            )
        log_info(f"Dashboard generated: '{report_path}'")
        return report_path

    def _send_report_email(self, report_path: Path, branch: str) -> None:
        recipients = self._parse_recipients(self.email_to_var.get().strip())
        if not recipients:
            raise ValueError(
                "Email recipients are empty.\n"
                "Please provide one or more recipients in 'Email recipients' separated by commas."
            )

        smtp_values = self._validate_smtp_config()
        smtp_host = smtp_values["SMTP_HOST"]
        smtp_port = int(smtp_values["SMTP_PORT"])
        smtp_username = smtp_values["SMTP_USERNAME"]
        smtp_password = smtp_values["SMTP_PASSWORD"]
        smtp_from = smtp_values["SMTP_FROM"]
        smtp_use_ssl = config_value("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes"}
        log_info(f"Send email: to={', '.join(recipients)} host={smtp_host}:{smtp_port} ssl={smtp_use_ssl}")

        msg = EmailMessage()
        msg["Subject"] = f"QA Metrics Dashboard ({branch})"
        msg["From"] = smtp_from
        msg["To"] = ", ".join(recipients)
        msg.set_content("Automated QA metrics report is attached as HTML.")

        mime_type, _ = mimetypes.guess_type(str(report_path))
        main_type, sub_type = (mime_type or "text/html").split("/", 1)
        msg.add_attachment(report_path.read_bytes(), maintype=main_type, subtype=sub_type, filename=report_path.name)

        if smtp_use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as smtp:
                smtp.login(smtp_username, smtp_password)
                smtp.send_message(msg)
            log_info("Email sent successfully (SMTP SSL)")
            return

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(smtp_username, smtp_password)
            smtp.send_message(msg)
        log_info("Email sent successfully (SMTP STARTTLS)")

    def _run_worker(
        self,
        download: bool,
        only_allure_results: bool = False,
        generate_report: bool = False,
        send_email: bool = False,
    ) -> None:
        self._set_buttons_enabled(False)
        self._set_progress_indeterminate(True)

        def work() -> None:
            try:
                owner, repo, branch, days, output = self._validate()
                client = GithubArtifactsClient(self.token_var.get(), owner, repo)
                self.after(0, lambda: self._set_status(f"Loading artifacts from branch '{branch}'..."))
                artifacts = client.list_artifacts(branch=branch, days=days)
                self.after(0, lambda: self._insert_artifacts(artifacts))

                if not artifacts:
                    self.after(0, lambda: self._set_progress_indeterminate(False))
                    self.after(0, lambda: self._set_status("No artifacts found"))
                    return

                if download:
                    downloadable = [artifact for artifact in artifacts if not artifact.expired]
                    if only_allure_results:
                        downloadable = [
                            artifact for artifact in downloadable if "allure-results" in artifact.name.lower()
                        ]
                    self.after(0, lambda: self._set_progress(0, len(downloadable) * 100))

                    if not downloadable:
                        if only_allure_results:
                            self.after(
                                0, lambda: self.
                                _set_status(f"Found {len(artifacts)} artifacts, 0 downloadable allure-results")
                            )
                        else:
                            self.after(
                                0,
                                lambda: self._set_status(f"Found {len(artifacts)} artifacts, 0 downloadable (expired)")
                            )
                        return

                    downloaded = 0
                    for index, artifact in enumerate(downloadable, start=1):
                        self.after(
                            0,
                            lambda i=index, total=len(downloadable), name=artifact.name: self.
                            _set_status(f"Downloading {i}/{total}: {name}")
                        )

                        last_ui_update = 0.0

                        def on_chunk(received: int, total_bytes: int) -> None:
                            nonlocal last_ui_update
                            now = time.monotonic()
                            if now - last_ui_update < 0.2:
                                return
                            last_ui_update = now

                            if total_bytes > 0:
                                file_percent = min(100, int(received * 100 / total_bytes))
                                overall = ((index - 1) * 100) + file_percent
                                self.after(0, lambda v=overall, m=len(downloadable) * 100: self._set_progress(v, m))
                                self.after(
                                    0,
                                    lambda i=index, total=len(downloadable), name=artifact.name, r=received, t=
                                    total_bytes: self._set_status(
                                        f"Downloading {i}/{total}: {name} ({self._format_size(r)} / {self._format_size(t)})"
                                    ),
                                )
                            else:
                                self.after(
                                    0,
                                    lambda i=index, total=len(downloadable), name=artifact.name, r=received: self.
                                    _set_status(f"Downloading {i}/{total}: {name} ({self._format_size(r)})"),
                                )

                        client.download_artifact(artifact, output, progress_cb=on_chunk)
                        downloaded += 1
                        self.after(0, lambda v=index * 100, m=len(downloadable) * 100: self._set_progress(v, m))
                    if only_allure_results:
                        self.after(
                            0, lambda: self.
                            _set_status(f"Found {len(artifacts)} artifacts, downloaded {downloaded} allure-results")
                        )
                    else:
                        self.after(
                            0, lambda: self._set_status(f"Found {len(artifacts)} artifacts, downloaded {downloaded}")
                        )

                    if generate_report:
                        self.after(0, lambda: self._set_progress_indeterminate(True))
                        self.after(0, lambda: self._set_status("Generating metrics dashboard..."))
                        report_path = self._generate_dashboard(output, branch)
                        if send_email:
                            self.after(0, lambda: self._set_status("Sending report via email..."))
                            self._send_report_email(report_path, branch)
                            self.after(0, lambda p=report_path: self._set_status(f"Report generated and emailed: {p}"))
                        else:
                            try:
                                webbrowser.open(report_path.resolve().as_uri())
                                self.after(
                                    0, lambda p=report_path: self._set_status(f"Report generated and opened: {p}")
                                )
                            except Exception:  # noqa: BLE001
                                self.after(0, lambda p=report_path: self._set_status(f"Report generated: {p}"))
                        self.after(0, lambda: self._set_progress_indeterminate(False))
                else:
                    self.after(0, lambda: self._set_progress_indeterminate(False))
                    self.after(0, lambda: self._set_status(f"Found {len(artifacts)} artifacts"))
            except Exception as exc:  # noqa: BLE001
                log_info(f"Generate report flow failed: {exc}")
                self.after(0, lambda: self._set_progress_indeterminate(False))
                self.after(0, lambda err=exc: messagebox.showerror("Error", str(err)))
                self.after(0, lambda: self._set_status("Failed"))
            finally:
                self.after(0, lambda: self._set_buttons_enabled(True))

        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    print("Starting GitHub Artifacts Collector UI...")
    try:
        app = App()
        app.mainloop()
    except tk.TclError as exc:
        print(f"Failed to start Tk UI: {exc}")
        print("Tkinter GUI is unavailable in this environment (no display or missing Tk runtime).")
        raise SystemExit(1)
