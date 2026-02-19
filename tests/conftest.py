import sys
from pathlib import Path

# Remove bundled local runtime path from import resolution during tests.
repo_root = Path(__file__).resolve().parents[1]
bundled = str(repo_root / 'python' / 'Lib' / 'site-packages')
if bundled in sys.path:
    sys.path.remove(bundled)
