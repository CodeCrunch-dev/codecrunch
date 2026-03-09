"""Tests for the CodeCrunch ingestion module."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.ingestion import ingest_repo


def test_ingest_repo():
    """Run ingest_repo on sample_repo/ and verify results."""
    sample_repo_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sample_repo"
    )

    result = ingest_repo(sample_repo_path)

    print("Files found:", result["files_found"])
    for file_info in result["files"]:
        print(f"  {file_info['filepath']}")
        print(f"    imports: {file_info['imports']}")

    # All 5 sample_repo Python files should be found
    expected_files = {"config.py", "database.py", "models.py", "utils.py", "main.py"}
    found_basenames = {os.path.basename(f["filepath"]) for f in result["files"]}
    assert found_basenames == expected_files, f"Expected {expected_files}, got {found_basenames}"
    assert result["files_found"] == 5

    # No __pycache__ or .git paths should appear
    all_paths = " ".join(f["filepath"] for f in result["files"])
    assert "__pycache__" not in all_paths, "__pycache__ should not appear in results"
    assert ".git" not in all_paths, ".git should not appear in results"
    assert "temp" not in all_paths, "temp/ (gitignored) should not appear in results"
    assert "debug.log" not in all_paths, "*.log (gitignored) should not appear in results"

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_ingest_repo()
