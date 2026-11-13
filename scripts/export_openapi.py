"""Write the API's OpenAPI document to frontend/openapi.json.

The frontend generates its TypeScript types from this file (`npm run gen:api`),
so frontend and backend cannot silently drift apart. CI re-runs this and fails if
the committed file is out of date.

Usage:  python scripts/export_openapi.py
"""

import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Importing the app needs settings, but no database connection or real secret.
os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(48))
os.environ.setdefault("DB_PASSWORD", "unused-for-export")

from app.main import app  # noqa: E402

target = ROOT / "frontend" / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
print(f"Wrote {target.relative_to(ROOT)}")
