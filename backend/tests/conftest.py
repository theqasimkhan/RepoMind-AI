"""Test path setup for monorepo imports (vector-store, ai_engine)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _name in ("vector-store", "ai_engine"):
    _p = _ROOT / _name
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
