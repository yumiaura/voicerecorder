#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project-wide environment and path constants (loaded at import)."""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

TRUE_VALUES = ("1", "true", "yes", "on", "enabled")

PROJ_ROOT = Path(__file__).resolve().parent

RECORD_DIR = os.getenv("RECORD_DIR", str(PROJ_ROOT / "data" / "recordings"))
SEGMENT_MINUTES = int(os.getenv("SEGMENT_MINUTES", "5"))
PULSE_SOURCE = (os.getenv("PULSE_SOURCE") or "").strip()
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "48000"))

SQLITE_PATH = os.getenv("SQLITE_PATH", str(PROJ_ROOT / "data" / "app.db"))

STT_ENABLED = (os.getenv("STT_ENABLED", "0").lower() in TRUE_VALUES)
STT_URL = os.getenv("STT_URL", "http://localhost:5099").rstrip("/")
STT_INTERVAL_SEC = int(os.getenv("STT_INTERVAL_SEC", "5"))
STT_USE_WAV = (os.getenv("STT_USE_WAV", "0").lower() in TRUE_VALUES)
STT_REQUEST_TIMEOUT_SEC = int(os.getenv("STT_REQUEST_TIMEOUT_SEC", "600"))

STT_ADD_PENDING = STT_ENABLED

# Local web UI / API (JWT, HS256)
SECRET_KEY = os.getenv("SECRET_KEY", "***REMOVED***")
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin")
AUTH_JWT_HOURS = int(os.getenv("AUTH_JWT_HOURS", "168"))


def main() -> None:
    pass


if __name__ == "__main__":
    main()
