import sys
from pathlib import Path


def pytest_configure(config):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
