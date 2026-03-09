"""Tests for the CodeCrunch artifact module."""

import os
import sys
import xml.etree.ElementTree as ET

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.ingestion import ingest_repo
from codecrunch.import_analyzer import build_dependency_graph
from codecrunch.artifact import build_artifact, save_artifact, load_artifact


def test_artifact():
    """Run full pipeline, save artifact, verify round-trip."""
    project_root = os.path.dirname(os.path.dirname(__file__))
    sample_repo_path = os.path.join(project_root, "sample_repo")
    output_path = os.path.join(project_root, "sample_repo.codecrunch")

    # Full pipeline
    repo_data = ingest_repo(sample_repo_path)
    dependency_graph = build_dependency_graph(repo_data)
    xml_string = build_artifact(repo_data, dependency_graph)

    # Save artifact
    save_artifact(xml_string, output_path)

    # Print full XML output
    print("Full XML output:")
    print("-" * 60)
    print(xml_string)
    print("-" * 60)

    # Assert XML is valid (parseable)
    ET.fromstring(xml_string)
    print("XML is valid (parseable)")

    # Load and verify round-trip
    loaded = load_artifact(output_path)

    assert "metadata" in loaded
    assert loaded["metadata"]["files_count"] == 5
    print(f"Round-trip: files_count = {loaded['metadata']['files_count']}")

    expected_paths = {"config.py", "database.py", "main.py", "models.py", "utils.py"}
    loaded_paths = {m["path"] for m in loaded["modules"]}
    assert loaded_paths == expected_paths
    print(f"Round-trip: all module paths present: {loaded_paths}")

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_artifact()
