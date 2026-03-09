#!/usr/bin/env python3
"""Run the full CodeCrunch Phase 1 pipeline end-to-end."""

import argparse
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codecrunch.ingestion import ingest_repo
from codecrunch.import_analyzer import build_dependency_graph, print_dependency_graph
from codecrunch.artifact import build_artifact, save_artifact
from codecrunch.summarizer import summarize_repo, inject_summaries


def main():
    parser = argparse.ArgumentParser(description="CodeCrunch Phase 1 pipeline")
    parser.add_argument(
        "repo_path",
        nargs="?",
        default="sample_repo",
        help="Path to the repository to analyze (default: sample_repo)",
    )
    args = parser.parse_args()

    repo_path = os.path.abspath(args.repo_path)
    if not os.path.isdir(repo_path):
        print(f"Error: {repo_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    repo_name = os.path.basename(repo_path.rstrip(os.sep))
    output_path = os.path.join(os.getcwd(), f"{repo_name}.codecrunch")

    # 1. Ingest
    repo_data = ingest_repo(repo_path)

    # 2. Build dependency graph
    dependency_graph = build_dependency_graph(repo_data)

    # 3. Print dependency graph
    print_dependency_graph(dependency_graph)

    # 4. Build artifact
    xml_string = build_artifact(repo_data, dependency_graph)

    # 5. Summarize (mock mode)
    summaries = summarize_repo(repo_data, mock=True)

    # 6. Inject summaries
    xml_final = inject_summaries(xml_string, summaries)

    # 7. Save
    save_artifact(xml_final, output_path)

    # 8. Summary
    files_processed = repo_data["files_found"]
    edges_found = len(dependency_graph["edges"])
    artifact_size = len(xml_final.encode("utf-8"))

    print("\n" + "=" * 40)
    print("Pipeline complete")
    print("=" * 40)
    print(f"Files processed:  {files_processed}")
    print(f"Edges found:      {edges_found}")
    print(f"Artifact size:    {artifact_size} bytes")
    print(f"Output path:      {output_path}")


if __name__ == "__main__":
    main()
