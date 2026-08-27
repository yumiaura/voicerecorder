#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record audio to timed Ogg Vorbis segments in RECORD_DIR."""

import logging
import os
import sys
import subprocess
import time
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

# Local imports
import config
from api.models import create_tables, TIMEZONE
from api.segment_registrar import register_segment

LOG_DIR = Path(config.LOG_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "handlers": [
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_DIR / "recorder.log",
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding="utf-8",
        ),
    ],
    "format": (
        "%(asctime)s.%(msecs)03d [%(levelname)s]: "
        "(%(name)s.%(funcName)s) %(message)s"
    ),
    "level": logging.INFO,
    "datefmt": "%Y-%m-%d %H:%M:%S",
}
logging.basicConfig(**LOGGING)
logger = logging.getLogger(__name__)


def recorder_input_args() -> tuple[str, str]:
    """Return ffmpeg input format/device from env config."""
    if config.RECORDER_INPUT == "alsa":
        source = config.ALSA_DEVICE
        # plughw is more tolerant for USB capture format negotiation.
        if source.startswith("hw:"):
            source = "plughw:" + source[3:]
        return "alsa", source
    if config.PULSE_SOURCE:
        return "pulse", config.PULSE_SOURCE
    return "pulse", "default"


def make_output_path() -> Path:
    now = datetime.now(TIMEZONE)
    day = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    d = Path(config.RECORD_DIR) / day
    d.mkdir(parents=True, exist_ok=True)
    return d / f"seg_{stamp}.ogg"


def run_ffmpeg(
    out_path: Path, duration_sec: int, source: str, input_format: str
) -> int:
    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-f",
        input_format,
        "-ac",
        str(config.RECORDER_CHANNELS),
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
    input_format, source = recorder_input_args()
    logger.info(
        "START segment file=%s input_format=%s source=%s duration_sec=%s",
        str(out),
        input_format,
        source,
        sec,
    )
    rc = run_ffmpeg(out, sec, source, input_format)
    t1 = datetime.now(TIMEZONE)
    if rc != 0 or not out.is_file():
        logger.error(
            "FINISH segment failed file=%s rc=%s elapsed_sec=%.2f",
            str(out),
            rc,
            (t1 - t0).total_seconds(),
        )
        return False
    reg = register_segment(str(out), t0, t1)
    if not reg:
        logger.error(
            "FINISH segment db_register_failed file=%s elapsed_sec=%.2f",
            str(out),
            (t1 - t0).total_seconds(),
        )
        return False
    logger.info(
        "FINISH segment ok file=%s elapsed_sec=%.2f",
        str(out),
        (t1 - t0).total_seconds(),
    )
    return True


def main() -> None:
    Path(config.RECORD_DIR).mkdir(parents=True, exist_ok=True)
    create_tables()
    input_format, source = recorder_input_args()
    logger.info(
        "Record loop RECORD_DIR=%s every %s min input_format=%s source=%s",
        config.RECORD_DIR,
        config.SEGMENT_MINUTES,
        input_format,
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
