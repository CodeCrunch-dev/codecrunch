"""Module for ingesting and loading source code files."""

import os
from pathlib import Path

from pathspec import PathSpec

from codecrunch.parser import extract_structure


DEFAULT_IGNORE_PATTERNS = [
    "__pycache__",
    ".git",
    "*.pyc",
    ".env",
    "node_modules",
    "venv",
    ".venv",
]

DEFAULT_TEST_PATH_SUBSTRINGS = [
    "/test/",
    "/tests/",
    "/__tests__/",
    "/spec/",
]

DEFAULT_EXCLUDE_FILENAMES = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Gemfile.lock",
]


def load_gitignore(repo_path: str) -> PathSpec:
    """
    Read .gitignore from the repo root if it exists.
    Always ignores: __pycache__, .git, *.pyc, .env, node_modules, venv, .venv
    Returns a compiled pathspec matcher.
    """
    patterns = DEFAULT_IGNORE_PATTERNS.copy()

    gitignore_path = os.path.join(repo_path, ".gitignore")
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)

    # pathspec's "gitignore" pattern is deprecated; "gitwildmatch" matches gitignore behavior.
    spec = PathSpec.from_lines("gitwildmatch", patterns)
    return spec


def _should_exclude_by_convention(
    rel_path_normalized: str,
    *,
    exclude_tests: bool,
    exclude_filenames: set[str],
    test_path_substrings: list[str],
) -> bool:
    if os.path.basename(rel_path_normalized) in exclude_filenames:
        return True
    if exclude_tests:
        path_lower = f"/{rel_path_normalized.lower().lstrip('/')}"
        for sub in test_path_substrings:
            if sub in path_lower:
                return True
    return False


def collect_files(
    repo_path: str,
    extensions: list[str] | None = None,
    *,
    exclude_tests: bool = False,
    exclude_filenames: list[str] | None = None,
    test_path_substrings: list[str] | None = None,
) -> list[str]:
    """
    Walk the repo directory recursively.
    Skip anything matched by the gitignore pathspec.
    Return a sorted list of relative file paths (relative to repo_path) matching the given extensions.
    """
    if extensions is None:
        extensions = [".py"]
    if exclude_filenames is None:
        exclude_filenames = DEFAULT_EXCLUDE_FILENAMES
    if test_path_substrings is None:
        test_path_substrings = DEFAULT_TEST_PATH_SUBSTRINGS

    spec = load_gitignore(repo_path)
    repo_path_resolved = os.path.abspath(repo_path)
    collected: list[str] = []
    exclude_filenames_set = {n for n in exclude_filenames}

    for root, dirs, files in os.walk(repo_path_resolved):
        # Prune ignored directories so we don't descend into them
        dirs[:] = [
            d for d in dirs
            if not spec.match_file(os.path.relpath(os.path.join(root, d), repo_path_resolved).replace(os.sep, "/"))
        ]
        for filename in files:
            if not any(filename.endswith(ext) for ext in extensions):
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, repo_path_resolved)
            # Normalize to forward slashes for pathspec (gitignore style)
            rel_path_normalized = rel_path.replace(os.sep, "/")

            if spec.match_file(rel_path_normalized):
                continue

            if _should_exclude_by_convention(
                rel_path_normalized,
                exclude_tests=exclude_tests,
                exclude_filenames=exclude_filenames_set,
                test_path_substrings=test_path_substrings,
            ):
                continue

            collected.append(rel_path)

    return sorted(collected)


def ingest_repo(
    repo_path: str,
    *,
    extensions: list[str] | None = None,
    exclude_tests: bool = False,
    exclude_filenames: list[str] | None = None,
    test_path_substrings: list[str] | None = None,
) -> dict:
    """
    Collect files and extract structure from each.
    Returns: {"repo_path": str, "files_found": int, "files": [list of extract_structure dicts]}
    """
    repo_path_resolved = os.path.abspath(repo_path)
    file_paths = collect_files(
        repo_path_resolved,
        extensions=extensions,
        exclude_tests=exclude_tests,
        exclude_filenames=exclude_filenames,
        test_path_substrings=test_path_substrings,
    )

    files = []
    for rel_path in file_paths:
        full_path = os.path.join(repo_path_resolved, rel_path)
        structure = extract_structure(full_path)
        files.append(structure)

    return {
        "repo_path": repo_path_resolved,
        "files_found": len(files),
        "files": files,
    }
