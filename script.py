from pathlib import Path
from datetime import datetime

# ===== НАСТРОЙКИ ПО УМОЛЧАНИЮ =====

SOURCE_DIR = Path(__file__).parent  # текущая папка
OUTPUT_FILE = SOURCE_DIR / "project_dump.txt"

ALLOWED_EXTENSIONS = {".py", ".md", ".txt"}

IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
}

IGNORE_FILES = {
    "__init__.py",
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".log",
    ".lock",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".exe",
    ".zip",
    ".tar",
    ".gz",
    ".pdf",
}

# ===== ЛОГИКА =====

def main():
    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        out.write(f"# Project dump\n")
        out.write(f"# Generated at: {datetime.now()}\n\n")

        for file in sorted(SOURCE_DIR.rglob("*")):
            if not file.is_file():
                continue

            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            if file.name in IGNORE_FILES:
                continue

            if file.suffix in IGNORE_EXTENSIONS:
                continue

            if file.suffix not in ALLOWED_EXTENSIONS:
                continue

            out.write("=" * 80 + "\n")
            out.write(f"FILE: {file.relative_to(SOURCE_DIR)}\n")
            out.write("=" * 80 + "\n")

            try:
                out.write(file.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                out.write("[SKIPPED: binary or non-utf8 file]")
            except Exception as e:
                out.write(f"[ERROR reading file: {e}]")

            out.write("\n\n")

    print(f"✅ Готово. Результат: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
