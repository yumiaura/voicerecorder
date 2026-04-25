#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record PulseAudio to timed Ogg Vorbis segments in RECORD_DIR."""

import logging
import os
import sys
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

# Local imports
import config
from api.models import create_tables, TIMEZONE
from api.segment_registrar import register_segment

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


def pulse_device_arg() -> str:
    if config.PULSE_SOURCE:
        return config.PULSE_SOURCE
    return "default"


def make_output_path() -> Path:
    now = datetime.now(TIMEZONE)
    day = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    d = Path(config.RECORD_DIR) / day
    d.mkdir(parents=True, exist_ok=True)
    return d / f"seg_{stamp}.ogg"


def run_ffmpeg(
    out_path: Path, duration_sec: int, source: str
) -> int:
    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-f",
        "pulse",
        "-i",
        source,
        "-t",
        str(duration_sec),
        "-c:a",
        "libvorbis",
        "-q:a",
        "5",
        "-ar",
        str(config.SAMPLE_RATE),
        str(out_path),
    ]
    logger.info("Running ffmpeg: %s", " ".join(cmd))
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=duration_sec + 120,
    )
    if p.returncode != 0:
        log_out = p.stdout.decode("utf-8", errors="replace") if p.stdout else ""
        logger.error("ffmpeg failed rc=%s: %s", p.returncode, log_out[:4000])
    return int(p.returncode)


def one_segment() -> bool:
    sec = int(config.SEGMENT_MINUTES * 60)
    if sec < 1:
        logger.error("SEGMENT_MINUTES must yield positive seconds")
        return False
    out = make_output_path()
    t0 = datetime.now(TIMEZONE)
    source = pulse_device_arg()
    rc = run_ffmpeg(out, sec, source)
    t1 = datetime.now(TIMEZONE)
    if rc != 0 or not out.is_file():
        return False
    reg = register_segment(str(out), t0, t1)
    if not reg:
        return False
    return True


def main() -> None:
    Path(config.RECORD_DIR).mkdir(parents=True, exist_ok=True)
    create_tables()
    source = pulse_device_arg()
    logger.info(
        "Record loop RECORD_DIR=%s every %s min source=%s",
        config.RECORD_DIR,
        config.SEGMENT_MINUTES,
        source,
    )
    while True:
        try:
            ok = one_segment()
            if not ok:
                time.sleep(5.0)
        except KeyboardInterrupt:
            raise
        except Exception as exc:  # pragma: no cover
            logger.error(
                "segment loop: %s: %s", type(exc).__name__, str(exc)
            )
            logger.error("%s", traceback.format_exc())
            time.sleep(5.0)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info("record.py stop: %s", type(e).__name__)
