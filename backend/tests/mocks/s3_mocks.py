"""
Mock S3 responses for testing directory loading.

Simulates reading directory.json from S3 without real AWS calls.
"""

import json
from pathlib import Path


def load_mock_directory() -> dict:
    """Load the actual directory.json from the data/ directory for testing."""
    directory_path = Path(__file__).parent.parent.parent.parent / "data" / "directory.json"
    if directory_path.exists():
        with open(directory_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": "test", "resources": []}
