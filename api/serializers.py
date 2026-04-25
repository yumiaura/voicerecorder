#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSON response serializers (pure functions)."""

import os
from datetime import date, datetime
from typing import Any, Dict, Optional, Union

import pytz

from api.models import Segment

TIMEZONE = pytz.timezone(os.getenv("TZ", "UTC"))

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def format_datetime(
    dt: Optional[Union[datetime, date]],
) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            aware = TIMEZONE.localize(dt)
        else:
            aware = dt.astimezone(TIMEZONE)
        return aware.strftime(DATETIME_FMT)
    return str(dt)


def segment_serializer(s: Segment) -> Dict[str, Any]:
    return {
        "id": s.id,
        "file_name": s.file_name,
        "segment_start": format_datetime(s.segment_start),
        "segment_end": format_datetime(s.segment_end),
        "bytes_size": s.bytes_size,
        "duration_sec": s.duration_sec,
        "transcript": s.transcript,
        "stt_status": s.stt_status,
        "stt_error": s.stt_error,
        "stt_at": format_datetime(s.stt_at) if s.stt_at else None,
        "stream_url": f"/api/stream/{s.id}",
    }


def main() -> None:
    pass


if __name__ == "__main__":
    main()
