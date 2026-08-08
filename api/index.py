import sys
import os

# Ensure root directory and backend directory are in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")

for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend.main import app
