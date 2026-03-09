"""Tests for the CodeCrunch parser module."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codecrunch.parser import parse_file, extract_structure


def test_parse_file_config():
    """Test parse_file on sample_repo/config.py."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sample_repo", "config.py"
    )
    root = parse_file(config_path)
    assert root is not None
    assert root.type == "module"
    print("parse_file(config.py) - root node type:", root.type)


def test_extract_structure_config():
    """Test extract_structure on sample_repo/config.py."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sample_repo", "config.py"
    )
    result = extract_structure(config_path)
    assert "filepath" in result
    assert "functions" in result
    assert "classes" in result
    assert "imports" in result
    assert result["filepath"] == config_path
    assert result["functions"] == []
    assert result["classes"] == []
    assert result["imports"] == []
    print("extract_structure(config.py):", result)


def test_parse_file_main():
    """Test parse_file on sample_repo/main.py."""
    main_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sample_repo", "main.py"
    )
    root = parse_file(main_path)
    assert root is not None
    assert root.type == "module"
    print("parse_file(main.py) - root node type:", root.type)


def test_extract_structure_main():
    """Test extract_structure on sample_repo/main.py."""
    main_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sample_repo", "main.py"
    )
    result = extract_structure(main_path)
    assert "filepath" in result
    assert "functions" in result
    assert "classes" in result
    assert "imports" in result
    assert result["filepath"] == main_path
    assert "main" in result["functions"]
    assert len(result["imports"]) >= 2  # from utils import ... and from models import ...
    print("extract_structure(main.py):", result)


if __name__ == "__main__":
    test_parse_file_config()
    test_extract_structure_config()
    test_parse_file_main()
    test_extract_structure_main()
    print("\nAll tests passed!")
