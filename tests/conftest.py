import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS_DIR = ROOT / "tests"

# Remove the tests directory from sys.path so it doesn't shadow real packages
if str(TESTS_DIR) in sys.path:
    sys.path.remove(str(TESTS_DIR))

# Prepend source and repo root for absolute imports (organ_chip, organchip, src.*)
for path in (SRC, ROOT):
    if path.exists():
        path_str = str(path)
        if path_str in sys.path:
            sys.path.remove(path_str)
        sys.path.insert(0, path_str)

