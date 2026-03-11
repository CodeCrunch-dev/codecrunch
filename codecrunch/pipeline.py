"""End-to-end pipeline assembler for CodeCrunch artifacts (Phase 2)."""

from __future__ import annotations

import os

from codecrunch.artifact import build_artifact
from codecrunch.ingestion import ingest_repo
from codecrunch.import_analyzer import build_dependency_graph
from codecrunch.patterns import cluster_repo
from codecrunch.summarizer import inject_summaries, summarize_repo
from codecrunch.token_count import count_tokens


DEFAULT_EXTENSIONS = [".py", ".js", ".jsx", ".ts", ".tsx"]


def run(
    repo_path: str,
    *,
    extensions: list[str] | None = None,
    exclude_tests: bool = True,
    mock_summaries: bool = True,
    batch_size: int = 10,
    pattern_depth: int = 4,
    pattern_threshold: float = 0.85,
) -> tuple[str, dict]:
    """
    Run the full pipeline and return (xml_string, metrics).
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    repo_path_abs = os.path.abspath(repo_path)

    repo_data = ingest_repo(repo_path_abs, extensions=extensions, exclude_tests=exclude_tests)
    dependency_graph = build_dependency_graph(repo_data)

    clusters = cluster_repo(repo_data, depth=pattern_depth, threshold=pattern_threshold)
    patterns = [
        {
            "id": c.cluster_id,
            "representative": c.representative,
            "members": c.members,
            "threshold": c.similarity_threshold,
            "fingerprint": c.fingerprint_hash,
        }
        for c in clusters
    ]

    xml_string = build_artifact(repo_data, dependency_graph, patterns=patterns)

    summaries = summarize_repo(repo_data, mock=mock_summaries, batch_size=batch_size)
    xml_final = inject_summaries(xml_string, summaries)

    # Token metrics: raw (included files only) vs artifact.
    raw_text_parts: list[str] = []
    for f in repo_data["files"]:
        try:
            with open(f["filepath"], "r", encoding="utf-8") as fp:
                raw_text_parts.append(fp.read())
        except OSError:
            continue
    raw_text = "\n".join(raw_text_parts)

    metrics = {
        "files_processed": repo_data["files_found"],
        "edges_found": len(dependency_graph["edges"]),
        "dependency_graph": dependency_graph,
        "patterns_clusters": len(patterns),
        "patterns_largest_cluster": max((len(p["members"]) for p in patterns), default=0),
        "raw_tokens": count_tokens(raw_text),
        "artifact_tokens": count_tokens(xml_final),
        "artifact_bytes": len(xml_final.encode("utf-8")),
    }

    return xml_final, metrics
