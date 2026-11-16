"""Test package; expose project modules for the existing algorithm tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "src", ROOT / "tests"):
    path = str(directory)
    if path not in sys.path:
        sys.path.insert(0, path)
