"""Module for analyzing import relationships between modules."""

import re
import os


def _extract_module_name(import_string: str) -> str | None:
    """Extract the module name from an import string."""
    import_string = import_string.strip()
    # "from X import Y" or "from X.Y import Z"
    from_match = re.match(r"from\s+(.+?)\s+import", import_string)
    if from_match:
        return from_match.group(1).strip()
    # "import X" or "import X as Y"
    import_match = re.match(r"import\s+(\S+)", import_string)
    if import_match:
        return import_match.group(1).strip()
    return None


def _module_to_candidate_paths(module_name: str) -> list[str]:
    """Convert a module name to possible file paths in the repo."""
    # "config" -> ["config.py", "config/__init__.py"]
    # "foo.bar" -> ["foo/bar.py", "foo/bar/__init__.py"]
    parts = module_name.split(".")
    candidates = [
        "/".join(parts) + ".py",
        "/".join(parts) + "/__init__.py",
    ]
    return candidates


def resolve_import(import_string: str, repo_files: list[str], repo_path: str) -> str | None:
    """
    Resolve an import string to an internal file path.

    Takes an import string like "from config import DATABASE_URL, DEBUG" or "import utils".
    Extracts the module name and checks if it matches any file in the repo.
    Returns the relative filepath if internal, None if external.
    """
    module_name = _extract_module_name(import_string)
    if not module_name:
        return None

    # Normalize repo_files to use forward slashes for matching
    repo_files_normalized = {f.replace(os.sep, "/") for f in repo_files}

    for candidate in _module_to_candidate_paths(module_name):
        if candidate in repo_files_normalized:
            return candidate
    return None


_RE_ESM_SPECIFIER = re.compile(
    r"""^\s*(?:import|export)\s+(?:.+?\s+from\s+)?['"]([^'"]+)['"]\s*;?\s*$"""
)
_RE_REQUIRE_SPECIFIER = re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)""")


def _extract_js_ts_specifier(import_string: str) -> str | None:
    s = import_string.strip()
    if s.startswith("require:"):
        return s.split(":", 1)[1].strip()
    m = _RE_ESM_SPECIFIER.match(s)
    if m:
        return m.group(1).strip()
    m = _RE_REQUIRE_SPECIFIER.search(s)
    if m:
        return m.group(1).strip()
    return None


def _js_ts_candidate_paths(from_rel: str, specifier: str) -> list[str]:
    """
    Resolve a relative JS/TS specifier to possible repo-relative file paths.

    We intentionally do not support tsconfig path aliases or package.json exports here.
    """
    if not (specifier.startswith("./") or specifier.startswith("../")):
        return []

    base_dir = os.path.dirname(from_rel).replace(os.sep, "/")
    joined = os.path.normpath(os.path.join(base_dir, specifier)).replace(os.sep, "/")

    # If specifier already includes an extension, try it directly.
    _, ext = os.path.splitext(joined)
    if ext:
        return [joined]

    exts = [".ts", ".tsx", ".js", ".jsx"]
    candidates: list[str] = []
    for e in exts:
        candidates.append(joined + e)
    for e in exts:
        candidates.append(joined.rstrip("/") + "/index" + e)
    return candidates


def resolve_import_any(
    import_string: str,
    *,
    language: str,
    from_rel: str,
    repo_files_normalized: set[str],
) -> str | None:
    """
    Resolve an import string to an internal file path for supported languages.

    Returns the repo-relative filepath if internal, None if external/unknown.
    """
    if language == "python":
        module_name = _extract_module_name(import_string)
        if not module_name:
            return None
        for candidate in _module_to_candidate_paths(module_name):
            if candidate in repo_files_normalized:
                return candidate
        return None

    if language in {"javascript", "typescript", "tsx"}:
        spec = _extract_js_ts_specifier(import_string)
        if not spec:
            return None
        for candidate in _js_ts_candidate_paths(from_rel, spec):
            if candidate in repo_files_normalized:
                return candidate
        return None

    return None


def build_dependency_graph(repo_data: dict) -> dict:
    """
    Build a dependency graph from ingest_repo output.

    Returns dict with nodes, edges, and external_imports.
    Uses relative paths (relative to repo_path) for all node names and edges.
    """
    repo_path = repo_data["repo_path"]
    files = repo_data["files"]

    # Build list of relative paths for repo files
    repo_files = []
    file_to_rel = {}
    for f in files:
        full_path = f["filepath"]
        rel_path = os.path.relpath(full_path, repo_path)
        rel_path_normalized = rel_path.replace(os.sep, "/")
        repo_files.append(rel_path_normalized)
        file_to_rel[full_path] = rel_path_normalized

    nodes = sorted(repo_files)
    edges = []
    external_imports = {rel: [] for rel in repo_files}
    repo_files_normalized = {p.replace(os.sep, "/") for p in repo_files}

    for file_info in files:
        from_rel = file_to_rel[file_info["filepath"]]
        language = file_info.get("language", "python")
        for import_str in file_info["imports"]:
            to_rel = resolve_import_any(
                import_str,
                language=language,
                from_rel=from_rel,
                repo_files_normalized=repo_files_normalized,
            )
            if to_rel is not None:
                edges.append({"from": from_rel, "to": to_rel})
            else:
                external_imports[from_rel].append(import_str)

    return {
        "nodes": nodes,
        "edges": edges,
        "external_imports": external_imports,
    }


def print_dependency_graph(graph: dict) -> None:
    """Pretty print the dependency graph."""
    print("Dependency Graph")
    print("=" * 40)
    print("Nodes:", ", ".join(graph["nodes"]))
    print()
    print("Edges (dependencies):")
    for edge in graph["edges"]:
        print(f"  {edge['from']} -> {edge['to']}")
    print()
    print("External imports (by file):")
    for node, imports in graph["external_imports"].items():
        if imports:
            print(f"  {node}: {imports}")
        else:
            print(f"  {node}: (none)")
