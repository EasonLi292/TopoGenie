import sys
from pathlib import Path

# Add the src directory to PYTHONPATH so tests can import topozero package
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if SRC_PATH not in map(Path, sys.path):
    sys.path.insert(0, str(SRC_PATH))
