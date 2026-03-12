from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import requests

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30


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
        self.token_var = tk.StringVar(value=token_from_env_file or os.getenv("GITHUB_TOKEN", ""))
        self.owner_var = tk.StringVar(value=default_owner)
        self.repo_var = tk.StringVar(value=default_repo)
        self.branch_var = tk.StringVar(value="main")
        self.days_var = tk.StringVar(value="7")
        self.output_var = tk.StringVar(value=str(Path.cwd() / "downloaded_artifacts"))

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

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(12, 8))
        self.find_btn = ttk.Button(btn_frame, text="Find artifacts", command=self._run_find)
        self.find_btn.pack(side=tk.LEFT)
        self.download_btn = ttk.Button(btn_frame, text="Find + download", command=self._run_download)
        self.download_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.download_allure_btn = ttk.Button(
            btn_frame,
            text="Download only allure-results",
            command=self._run_download_allure_results,
        )
        self.download_allure_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.generate_report_btn = ttk.Button(
            btn_frame,
            text="Generate report",
            command=self._run_generate_report,
        )
        self.generate_report_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(frm, mode="determinate", maximum=100)
        self.progress.grid(row=5, column=0, columnspan=4, sticky="ew")

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
        self.tree.grid(row=6, column=0, columnspan=4, sticky="nsew")

        self.status = tk.StringVar(value="Ready")
        ttk.Label(frm, textvariable=self.status).grid(row=7, column=0, columnspan=4, sticky="w", pady=(8, 0))

        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(3, weight=1)
        frm.grid_rowconfigure(6, weight=1)

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
        self.find_btn.configure(state=state)
        self.download_btn.configure(state=state)
        self.download_allure_btn.configure(state=state)
        self.generate_report_btn.configure(state=state)

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

    def _run_find(self) -> None:
        self._run_worker(download=False)

    def _run_download(self) -> None:
        self._run_worker(download=True, only_allure_results=False)

    def _run_download_allure_results(self) -> None:
        self._run_worker(download=True, only_allure_results=True)

    def _run_generate_report(self) -> None:
        self._run_worker(download=True, only_allure_results=True, generate_report=True)

    def _generate_dashboard(self, artifacts_dir: Path, branch: str) -> Path:
        script_path = Path(__file__).with_name("build_flaky_dashboard.py")
        report_path = Path.cwd() / "reports" / "metrics_dashboard.html"
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
            raise RuntimeError(f"Failed to generate dashboard: {details}")
        return report_path

    def _run_worker(self, download: bool, only_allure_results: bool = False, generate_report: bool = False) -> None:
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
                        try:
                            webbrowser.open(report_path.resolve().as_uri())
                            self.after(0, lambda p=report_path: self._set_status(f"Report generated and opened: {p}"))
                        except Exception:  # noqa: BLE001
                            self.after(0, lambda p=report_path: self._set_status(f"Report generated: {p}"))
                        self.after(0, lambda: self._set_progress_indeterminate(False))
                else:
                    self.after(0, lambda: self._set_progress_indeterminate(False))
                    self.after(0, lambda: self._set_status(f"Found {len(artifacts)} artifacts"))
            except Exception as exc:  # noqa: BLE001
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
