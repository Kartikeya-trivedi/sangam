"""Compatibility shim — the canonical loader is seed_dataset.py.

Kept because CLAUDE.md / docker docs reference this filename. Delegates to seed_dataset.main(),
which loads all 2,500 synthetic records into the SQLite registry (lost/found split).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_dataset import main  # noqa: E402

if __name__ == "__main__":
    main()
