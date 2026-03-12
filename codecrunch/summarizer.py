"""Module for summarizing code structure and relationships."""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def build_summary_prompt(filepath: str, source_code: str, structure: dict) -> str:
    """
    Build a prompt for an LLM to summarize a Python module.

    Returns a prompt string designed to produce a compressed summary.
    """
    structure_str = (
        f"Classes: {structure.get('classes', [])}\n"
        f"Functions: {structure.get('functions', [])}\n"
        f"Imports: {structure.get('imports', [])}"
    )
    return f"""Summarize this Python module for a codebase overview artifact.

File: {filepath}

Structure:
{structure_str}

Source code:
```python
{source_code}
```

Instructions:
- Describe what this module does in 2-3 sentences max.
- List the key responsibilities.
- Note any important side effects, global state, or external dependencies.
- Keep the summary under 150 tokens.
- Focus on architectural role, not implementation details.

Summary:"""


def summarize_module(
    filepath: str, source_code: str, structure: dict, mock: bool = True
) -> str:
    """
    Generate a summary for a Python module.

    If mock=True, returns a realistic fake summary.
    If mock=False, calls the real API (TODO: wire up Claude in Phase 2).
    """
    if not mock:
        # TODO: Wire up Claude API in Phase 2
        raise NotImplementedError("Wire up Claude API in Phase 2")

    # Mock: generate realistic summary from filename and structure
    basename = os.path.splitext(os.path.basename(filepath))[0]
    classes = structure.get("classes", [])
    functions = structure.get("functions", [])
    imports = structure.get("imports", [])

    parts = []
    if basename == "config":
        parts.append(
            "Configuration module that defines DATABASE_URL, DEBUG, SECRET_KEY, and LOG_LEVEL constants."
        )
    elif basename == "database":
        parts.append(
            "Database connection and session management. Provides get_connection and close_connection."
        )
    elif basename == "models":
        parts.append(
            f"Data models. Defines {classes[0] if classes else 'entities'} and fetch_user for DB access."
        )
    elif basename == "utils":
        parts.append(
            "Utility functions for logging and response formatting."
        )
    elif basename == "main":
        parts.append(
            "Application entry point. Orchestrates startup, loads User via models, formats output via utils."
        )
    else:
        parts.append(f"Module {basename} with {len(functions)} functions, {len(classes)} classes.")

    if not imports:
        parts.append("Leaf dependency with no internal imports.")
    else:
        deps = []
        for imp in imports[:3]:
            imp = str(imp).strip()
            dep = None
            if imp.startswith("require:"):
                spec = imp.split(":", 1)[1]
                dep = spec.split("/")[-1].replace(".js", "").replace(".ts", "")
            elif " from " in imp:
                idx = imp.find(" from ")
                rest = imp[idx + 6 :].strip().strip("'\"").split("/")[-1]
                dep = rest.replace(".js", "").replace(".ts", "")
            elif imp.startswith("import ") and len(imp.split()) >= 2:
                dep = imp.split()[1].strip("'\"").split("/")[-1].replace(".js", "").replace(".ts", "")
            if dep:
                deps.append(dep)
        if deps:
            parts.append(f"Depends on: {', '.join(deps)}.")

    return " ".join(parts)


def _default_cache_path(repo_path: str) -> str:
    return os.path.join(repo_path, ".codecrunch_summaries_cache.json")


def _load_cache(cache_path: str) -> dict[str, Any]:
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return {}


def _save_cache(cache_path: str, cache: dict[str, Any]) -> None:
    tmp_path = str(Path(cache_path).with_suffix(".tmp"))
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=True, indent=2, sort_keys=True)
    os.replace(tmp_path, cache_path)


def _cache_key(rel_path: str, full_path: str, structure: dict) -> str:
    try:
        mtime = int(os.path.getmtime(full_path))
    except OSError:
        mtime = 0
    extractor_version = structure.get("extractor_version", "unknown")
    return f"{rel_path}|{mtime}|{extractor_version}"


def summarize_repo(
    repo_data: dict,
    mock: bool = True,
    *,
    batch_size: int = 10,
    cache_path: str | None = None,
) -> dict:
    """
    Summarize all modules in the repo.

    Returns dict mapping relative filepath -> summary string.
    """
    repo_path = repo_data["repo_path"]
    summaries = {}

    if cache_path is None:
        cache_path = _default_cache_path(repo_path)
    cache = _load_cache(cache_path) if cache_path else {}

    files = list(repo_data["files"])
    if batch_size <= 0:
        batch_size = 10

    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        for file_info in batch:
            full_path = file_info["filepath"]
            rel_path = os.path.relpath(full_path, repo_path).replace(os.sep, "/")

            key = _cache_key(rel_path, full_path, file_info)
            cached = cache.get(key)
            if isinstance(cached, str) and cached:
                summaries[rel_path] = cached
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            summary = summarize_module(full_path, source_code, file_info, mock=mock)
            summaries[rel_path] = summary
            cache[key] = summary

    if cache_path:
        try:
            _save_cache(cache_path, cache)
        except Exception:
            # Cache failures should not break the pipeline.
            pass

    return summaries


def inject_summaries(xml_string: str, summaries: dict) -> str:
    """
    Replace PLACEHOLDER summaries in the XML artifact with actual summaries.

    Returns the updated XML string.
    """
    root = ET.fromstring(xml_string)
    modules_elem = root.find("modules")
    if modules_elem is None:
        return xml_string

    for mod_elem in modules_elem.findall("module"):
        path = mod_elem.get("path", "")
        if path in summaries:
            summary_elem = mod_elem.find("summary")
            if summary_elem is not None:
                summary_elem.text = summaries[path]

    # Serialize back to string
    ET.indent(ET.ElementTree(root), space="  ")
    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
