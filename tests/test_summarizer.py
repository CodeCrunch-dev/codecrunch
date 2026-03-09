"""Tests for the CodeCrunch summarizer module."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.ingestion import ingest_repo
from codecrunch.import_analyzer import build_dependency_graph
from codecrunch.artifact import build_artifact, save_artifact
from codecrunch.summarizer import (
    summarize_repo,
    inject_summaries,
    build_summary_prompt,
)


def test_summarizer():
    """Run full pipeline with summarization and verify."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    sample_repo_path = os.path.join(project_root, "sample_repo")
    output_path = os.path.join(project_root, "sample_repo_summarized.codecrunch")

    # Full pipeline: ingest -> graph -> artifact -> summarize -> inject
    repo_data = ingest_repo(sample_repo_path)
    dependency_graph = build_dependency_graph(repo_data)
    xml_string = build_artifact(repo_data, dependency_graph)

    summaries = summarize_repo(repo_data, mock=True)
    xml_with_summaries = inject_summaries(xml_string, summaries)

    save_artifact(xml_with_summaries, output_path)

    # Print one example prompt
    first_file = repo_data["files"][0]
    with open(first_file["filepath"], "r", encoding="utf-8") as f:
        source = f.read()
    example_prompt = build_summary_prompt(
        first_file["filepath"], source, first_file
    )
    print("Example prompt (for config.py):")
    print("=" * 60)
    print(example_prompt)
    print("=" * 60)

    # Print final XML
    print("\nFinal XML with summaries injected:")
    print("-" * 60)
    print(xml_with_summaries)
    print("-" * 60)

    # Assert no PLACEHOLDER remains
    assert "PLACEHOLDER" not in xml_with_summaries, "No module should have PLACEHOLDER in summary"

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_summarizer()
