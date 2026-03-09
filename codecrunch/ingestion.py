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

    spec = PathSpec.from_lines("gitignore", patterns)
    return spec


def collect_files(repo_path: str, extensions: list[str] | None = None) -> list[str]:
    """
    Walk the repo directory recursively.
    Skip anything matched by the gitignore pathspec.
    Return a sorted list of relative file paths (relative to repo_path) matching the given extensions.
    """
    if extensions is None:
        extensions = [".py"]

    spec = load_gitignore(repo_path)
    repo_path_resolved = os.path.abspath(repo_path)
    collected: list[str] = []

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

            collected.append(rel_path)

    return sorted(collected)


def ingest_repo(repo_path: str) -> dict:
    """
    Collect all Python files and extract structure from each.
    Returns: {"repo_path": str, "files_found": int, "files": [list of extract_structure dicts]}
    """
    repo_path_resolved = os.path.abspath(repo_path)
    file_paths = collect_files(repo_path_resolved)

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
