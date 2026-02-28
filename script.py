import os
from pathlib import Path


EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".idea",
    ".venv",
    "venv",
    ".pytest_cache",
    "node_modules",
    ".mypy_cache",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".log",
    ".tmp",
    ".swp",
}


def should_exclude(path: Path) -> bool:
    # Исключаем директории
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True

    # Исключаем файлы по расширению
    if path.suffix in EXCLUDED_EXTENSIONS:
        return True

    return False


def collect_python_files(project_path: Path):
    for root, dirs, files in os.walk(project_path):
        # Фильтруем директории (чтобы не заходить в исключённые)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            file_path = Path(root) / file

            if should_exclude(file_path):
                continue

            if file_path.suffix == ".py":
                yield file_path


def build_output_file():
    # Директория, где лежит сам скрипт
    project_path = Path(__file__).resolve().parent
    output_path = project_path / "collected_tests.txt"

    with open(output_path, "w", encoding="utf-8") as out:
        for file_path in collect_python_files(project_path):
            # Не включаем сам выходной файл, если вдруг совпадёт
            if file_path.name == output_path.name:
                continue

            relative_path = file_path.relative_to(project_path)

            out.write("=" * 80 + "\n")
            out.write(f"FILE: {relative_path}\n")
            out.write("=" * 80 + "\n\n")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"[ERROR READING FILE: {e}]")

            out.write("\n\n\n")

    print(f"Done! Files collected into: {output_path}")


if __name__ == "__main__":
    build_output_file()