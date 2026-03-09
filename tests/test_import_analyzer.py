"""Tests for the CodeCrunch import analyzer module."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.ingestion import ingest_repo
from codecrunch.import_analyzer import build_dependency_graph, print_dependency_graph


def test_import_analyzer():
    """Run ingest_repo, build dependency graph, and verify."""
    sample_repo_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sample_repo"
    )

    repo_data = ingest_repo(sample_repo_path)
    graph = build_dependency_graph(repo_data)

    print_dependency_graph(graph)

    # main.py has edges to utils.py and models.py
    main_edges = [e for e in graph["edges"] if e["from"] == "main.py"]
    main_targets = {e["to"] for e in main_edges}
    assert "utils.py" in main_targets, f"main.py should depend on utils.py, got {main_targets}"
    assert "models.py" in main_targets, f"main.py should depend on models.py, got {main_targets}"

    # config.py has no outgoing edges (leaf node)
    config_outgoing = [e for e in graph["edges"] if e["from"] == "config.py"]
    assert len(config_outgoing) == 0, f"config.py should have no outgoing edges, got {config_outgoing}"

    # Total edges should be 5
    assert len(graph["edges"]) == 5, f"Expected 5 edges, got {len(graph['edges'])}"

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_import_analyzer()
