#!/usr/bin/env python3
"""Clone demo repos for benchmarking and demo purposes."""

import os
import subprocess
import sys

# Project root (parent of scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_REPOS_DIR = os.path.join(PROJECT_ROOT, "demo_repos")

REPOS = [
    ("https://github.com/pallets/flask", "flask", "Python web framework"),
    ("https://github.com/expressjs/express", "express", "JavaScript, Node.js framework"),
    ("https://github.com/tiangolo/fastapi", "fastapi", "Python, modern API framework"),
]

EXTENSIONS = (".py", ".js", ".ts")


def count_files(repo_path: str) -> int:
    """Count .py, .js, .ts files in repo (excluding common ignore dirs)."""
    count = 0
    skip_dirs = {"__pycache__", ".git", "node_modules", "venv", ".venv", "dist", "build"}
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if any(f.endswith(ext) for ext in EXTENSIONS):
                count += 1
    return count


def main() -> int:
    os.makedirs(DEMO_REPOS_DIR, exist_ok=True)
    print(f"Demo repos directory: {DEMO_REPOS_DIR}\n")

    for url, name, desc in REPOS:
        repo_path = os.path.join(DEMO_REPOS_DIR, name)
        if os.path.isdir(os.path.join(repo_path, ".git")):
            print(f"[SKIP] {name} already cloned ({desc})")
        else:
            print(f"[CLONE] {name} ({desc})...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", url, repo_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"  ERROR: {result.stderr}", file=sys.stderr)
                return 1

        count = count_files(repo_path)
        print(f"  File count (.py, .js, .ts): {count}\n")

    print("Done. Run CodeCrunch on each repo:")
    print("  python -m codecrunch demo_repos/flask")
    print("  python -m codecrunch demo_repos/express")
    print("  python -m codecrunch demo_repos/fastapi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
