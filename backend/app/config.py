"""Application configuration.

Kept minimal for Phase 1: no database, no auth, no external services.
"""

import os

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
).split(",")
