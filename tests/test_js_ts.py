"""Phase 2 tests: JS/TS parsing, dependency graph, patterns, and token counting."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.ingestion import ingest_repo
from codecrunch.import_analyzer import build_dependency_graph
from codecrunch.patterns import cluster_repo
from codecrunch.token_count import count_tokens


def test_js_ts_pipeline_primitives():
    project_root = os.path.dirname(os.path.dirname(__file__))
    repo_path = os.path.join(project_root, "sample_repo_js_ts")

    repo_data = ingest_repo(
        repo_path,
        extensions=[".js", ".ts"],
        exclude_tests=True,
    )

    # Fixture has 6 files.
    assert repo_data["files_found"] == 6

    # Basic parser extraction sanity for TS.
    by_rel = {}
    for f in repo_data["files"]:
        rel = os.path.relpath(f["filepath"], repo_data["repo_path"]).replace(os.sep, "/")
        by_rel[rel] = f

    assert "index.ts" in by_rel
    assert by_rel["index.ts"]["language"] == "typescript"
    assert any("import" in s for s in by_rel["index.ts"]["imports"])
    assert any("export" in s for s in by_rel["index.ts"].get("exports", []))

    graph = build_dependency_graph(repo_data)

    # index.ts -> util.ts
    edges_from_index = [e for e in graph["edges"] if e["from"] == "index.ts"]
    assert any(e["to"] == "util.ts" for e in edges_from_index)

    # service.js -> lib.js
    edges_from_service = [e for e in graph["edges"] if e["from"] == "service.js"]
    assert any(e["to"] == "lib.js" for e in edges_from_service)

    # External imports captured.
    extern_index = graph["external_imports"]["index.ts"]
    assert any("react" in s for s in extern_index)
    extern_service = graph["external_imports"]["service.js"]
    assert any("fs" in s for s in extern_service)

    clusters = cluster_repo(repo_data, threshold=0.85)
    members_flat = [m for c in clusters for m in c.members]
    assert "controller_a.ts" in members_flat
    assert "controller_b.ts" in members_flat

    # Token counting: non-zero and stable-ish.
    assert count_tokens("hello world") > 0


if __name__ == "__main__":
    test_js_ts_pipeline_primitives()
    print("All tests passed!")

