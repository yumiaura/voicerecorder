#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register new recording segments in the database (recorder and tests)."""

import logging
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Local imports
import config
from api.db import SQLITE
from api.models import Segment, TIMEZONE

logger = logging.getLogger(__name__)


def probe_duration_sec(path: str) -> Optional[float]:
    """Return audio duration in seconds from ffprobe, or None on failure."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            stderr=subprocess.STDOUT,
            timeout=60,
        )
        s = out.decode("utf-8", errors="replace").strip()
        if not s:
            return None
        return float(s)
    except Exception as exc:
        logger.warning(
            f"ffprobe failed for {path}: {type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}"
        )
        return None


def register_segment(
    file_path: str,
    segment_start: datetime,
    segment_end: datetime,
) -> Optional[Dict[str, Any]]:
    """
    Insert a row for a finished Ogg file. segment_* must be timezone-aware in TIMEZONE.
    """
    p = Path(file_path)
    if not p.is_file():
        logger.error(f"register_segment: file not found: {file_path}")
        return None

    if segment_start.tzinfo is None:
        s_start = TIMEZONE.localize(segment_start)
    else:
        s_start = segment_start.astimezone(TIMEZONE)
    if segment_end.tzinfo is None:
        s_end = TIMEZONE.localize(segment_end)
    else:
        s_end = segment_end.astimezone(TIMEZONE)
    s_start = s_start.replace(microsecond=0)
    s_end = s_end.replace(microsecond=0)
    segment_start = s_start.replace(tzinfo=None)
    segment_end = s_end.replace(tzinfo=None)

    size = p.stat().st_size
    duration = probe_duration_sec(str(p))

    if config.STT_ADD_PENDING:
        stt_status = "pending"
    else:
        stt_status = "skipped"

    with SQLITE:
        row = Segment.create(
            file_path=str(p.resolve()),
            file_name=p.name,
            segment_start=segment_start,
            segment_end=segment_end,
            bytes_size=size,
            duration_sec=duration,
            stt_status=stt_status,
        )
    return {
        "id": row.id,
        "file_name": row.file_name,
        "stt_status": row.stt_status,
    }


def main() -> None:
    pass


if __name__ == "__main__":
    main()
