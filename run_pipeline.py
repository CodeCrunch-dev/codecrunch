#!/usr/bin/env python3
"""Run the full CodeCrunch Phase 1 pipeline end-to-end."""

import argparse
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codecrunch.artifact import save_artifact
from codecrunch.import_analyzer import print_dependency_graph
from codecrunch.pipeline import run


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

    xml_final, metrics = run(repo_path, mock_summaries=True)

    # Print dependency graph
    print_dependency_graph(metrics["dependency_graph"])

    # Save
    save_artifact(xml_final, output_path)

    print("\n" + "=" * 40)
    print("Pipeline complete")
    print("=" * 40)
    print(f"Files processed:  {metrics['files_processed']}")
    print(f"Edges found:      {metrics['edges_found']}")
    print(f"Patterns:         {metrics['patterns_clusters']} clusters (largest={metrics['patterns_largest_cluster']})")
    print(f"Raw tokens:       {metrics['raw_tokens']}")
    print(f"Artifact tokens:  {metrics['artifact_tokens']}")
    print(f"Artifact size:    {metrics['artifact_bytes']} bytes")
    print(f"Output path:      {output_path}")


if __name__ == "__main__":
    main()
