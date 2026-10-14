"""Central paths and settings. CONTRACT FILE.

Every file-system path in the project comes from here - never build a path from
the current working directory, so the app and tests behave the same no matter
where they are launched from.

Override with environment variables:
  LMS_DATA_DIR  directory for runtime data   (default: <project root>/data)
  LMS_DB_PATH   SQLite database file         (default: <LMS_DATA_DIR>/library.db)
"""
import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent      # <root>/src/lms
PROJECT_ROOT = PACKAGE_DIR.parent.parent           # <root>  (requires editable install: pip install -e .)

DATA_DIR = Path(os.environ.get("LMS_DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.environ.get("LMS_DB_PATH", DATA_DIR / "library.db"))
SCHEMA_PATH = PACKAGE_DIR / "persistence" / "schema.sql"
