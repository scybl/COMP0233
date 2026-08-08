from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_MARKERS = (
    "u" + "cl",
    "rse" + "-with-python",
    "moo" + "dle",
)
TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".csv",
    ".cfile",
    ".fixed-cost",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
SKIPPED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}


def iter_project_text_files():
    for path in ROOT.rglob("*"):
        if any(part in SKIPPED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def test_project_text_has_no_external_source_markers():
    offenders = []
    for path in iter_project_text_files():
        text = path.read_text(encoding="utf-8").lower()
        if any(marker in text for marker in FORBIDDEN_MARKERS):
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []
