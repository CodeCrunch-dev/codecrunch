#!/usr/bin/env python3
"""Convenience wrapper: run the CodeCrunch CLI."""

import sys

# Ensure project root is on path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codecrunch.cli import main

if __name__ == "__main__":
    # Default to sample_repo if no args
    if len(sys.argv) == 1:
        sys.argv.append("sample_repo")
    main()
