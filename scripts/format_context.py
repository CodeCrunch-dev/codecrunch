#!/usr/bin/env python3
"""Format a .codecrunch file into the same readable context block as the VS Code extension."""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.artifact import load_artifact


def format_context(artifact: dict) -> str:
    """
    Format the artifact into a readable context block (Python equivalent of contextProvider.ts).
    """
    lines = []

    repo = artifact.get("repo", "unknown")
    meta = artifact.get("metadata", {})
    dg = artifact.get("dependency_graph", {})
    edges = dg.get("edges", [])
    modules = artifact.get("modules", [])

    lines.append("## CodeCrunch: Codebase Context")
    lines.append(f"Repository: {repo}")
    lines.append(f"Files: {meta.get('files_count', 0)} | Dependencies: {len(edges)}")
    lines.append("")

    # Build node -> depends_on from edges; include leaf nodes from modules
    outgoing: dict[str, list[str]] = {}
    for mod in modules:
        outgoing[mod.get("path", "")] = []
    for edge in edges:
        from_node = edge.get("from", "")
        to_node = edge.get("to", "")
        if from_node and to_node:
            outgoing.setdefault(from_node, []).append(to_node)

    # Architecture
    lines.append("### Architecture")
    for node in sorted(outgoing.keys()):
        deps = outgoing.get(node, [])
        if not deps:
            lines.append(f"  {node} (leaf)")
        else:
            lines.append(f"  {node} -> {', '.join(sorted(deps))}")
    lines.append("")

    # Module summaries
    lines.append("### Module Summaries")
    for mod in modules:
        path = mod.get("path", "")
        summary = mod.get("summary", "(no summary)")
        lines.append(f"{path}: {summary}")

    return "\n".join(lines)


def main() -> int:
    import re

    parser = argparse.ArgumentParser(description="Format .codecrunch file as context block")
    parser.add_argument("filepath", help="Path to .codecrunch file")
    args = parser.parse_args()

    if not os.path.isfile(args.filepath):
        print(f"Error: {args.filepath} not found", file=sys.stderr)
        return 1

    artifact = load_artifact(args.filepath)

    # Parse repo from XML (load_artifact doesn't return it)
    with open(args.filepath, "r", encoding="utf-8") as f:
        content = f.read()
    repo_match = re.search(r'repo=["\']([^"\']*)["\']', content)
    if repo_match:
        artifact["repo"] = repo_match.group(1)
    else:
        artifact["repo"] = os.path.splitext(os.path.basename(args.filepath))[0].replace(".codecrunch", "")

    print(format_context(artifact))
    return 0


if __name__ == "__main__":
    sys.exit(main())
