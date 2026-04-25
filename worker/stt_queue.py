#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Poll the database for pending segments and call the STT HTTP service."""

import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Optional

import requests

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

# Local imports
import config
from api.models import Segment, create_tables, now_tz
from api.stt_transcribe import transcribe_segment_path

LOGGING = {
    "handlers": [logging.StreamHandler()],
    "format": (
        "%(asctime)s.%(msecs)03d [%(levelname)s]: "
        "(%(name)s.%(funcName)s) %(message)s"
    ),
    "level": logging.INFO,
    "datefmt": "%Y-%m-%d %H:%M:%S",
}
logging.basicConfig(**LOGGING)
logger = logging.getLogger(__name__)


def naive_now() -> datetime:
    n = now_tz()
    n = n.replace(microsecond=0)
    if n.tzinfo is not None:
        return n.replace(tzinfo=None)
    return n


def claim_one_pending() -> Optional[int]:
    """Return segment id to process, or None if nothing to do."""
    q = (
        Segment.select(Segment.id)
        .where(
            (Segment.stt_status == "pending")
            & (Segment.removed_at.is_null())
        )
        .order_by(Segment.id)
    )
    cand = q.get_or_none()
    if not cand:
        return None
    c = (
        Segment.update(
            {
                Segment.stt_status: "in_progress",
                Segment.updated_at: naive_now(),
            }
        )
        .where(
            (Segment.id == cand.id) & (Segment.stt_status == "pending")
        )
    ).execute()
    if c == 0:
        return None
    return int(cand.id)


def process_one(segment_id: int) -> None:
    s = Segment.get_by_id(segment_id)
    p = s.file_path
    if not os.path.isfile(p):
        msg = f"file missing: {p}"
        logger.error(msg)
        s.stt_status = "error"
        s.stt_error = msg
        s.stt_at = naive_now()
        s.save()
        return
    try:
        res = transcribe_segment_path(p)
    except Exception as exc:
        errt = f"{type(exc).__name__}: {str(exc)}"
        s.stt_status = "error"
        s.stt_error = errt
        s.stt_at = naive_now()
        s.transcript = None
        s.save()
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            b = (exc.response.text or "")[:800]
            logger.error("STT http err %s %s", exc.response.status_code, b)
        logger.error("STT error seg %s %s: %s", s.id, p, errt)
        logger.error("%s", traceback.format_exc())
        return
    txt = res.get("text", "")
    s.transcript = txt
    s.stt_status = "ok"
    s.stt_error = None
    s.stt_at = naive_now()
    s.save()
    server_elapsed = res.get("elapsed", "")
    base = os.path.basename(p)
    logger.info(
        "STT ok seg %s %s server=%r text_len=%s",
        s.id,
        base,
        server_elapsed,
        len(txt),
    )


def tick() -> None:
    sid = claim_one_pending()
    if sid is None:
        return
    process_one(sid)


def main() -> None:
    create_tables()
    if not config.STT_ENABLED:
        logger.info("STT is disabled in env; exiting stt_queue.")
        return
    logger.info("STT worker started. Press Ctrl+C to exit.")
    while True:
        try:
            tick()
        except Exception as exc:  # pragma: no cover
            logger.error("tick: %s: %s", type(exc).__name__, str(exc))
            logger.error("%s", traceback.format_exc())
        time.sleep(config.STT_INTERVAL_SEC)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info("stt_queue stop: %s", type(e).__name__)
