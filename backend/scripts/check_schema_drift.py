#!/usr/bin/env python
"""
Optional OpenAPI schema drift check for CI.

Usage (from backend/):
  python scripts/check_schema_drift.py
  python scripts/check_schema_drift.py --update

Compares the live spectacular schema to docs/openapi.snapshot.json
(repo-relative). Exit 1 on drift unless --update is passed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
SNAPSHOT = REPO_ROOT / "docs" / "openapi.snapshot.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Rewrite the snapshot from the current schema.",
    )
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.path.insert(0, str(BACKEND_DIR))

    import django

    django.setup()

    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    current_text = json.dumps(schema, indent=2, sort_keys=True, default=str) + "\n"

    if args.update or not SNAPSHOT.exists():
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(current_text, encoding="utf-8")
        print(f"Wrote schema snapshot -> {SNAPSHOT.relative_to(REPO_ROOT)}")
        return 0

    expected_text = SNAPSHOT.read_text(encoding="utf-8")
    if expected_text != current_text:
        print(
            "OpenAPI schema drift detected.\n"
            f"  Snapshot: {SNAPSHOT.relative_to(REPO_ROOT)}\n"
            "  Fix: python scripts/check_schema_drift.py --update\n"
            "  Then commit the updated snapshot if the change is intentional.",
            file=sys.stderr,
        )
        return 1

    print("OpenAPI schema matches snapshot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
