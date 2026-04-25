#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Call external STT HTTP API (multipart file upload)."""

import logging
import os
import subprocess
import tempfile
from typing import Any, Dict

import requests

# Local imports
import config

logger = logging.getLogger(__name__)


def transcribe_file(filepath: str) -> Dict[str, Any]:
    """Send a single file to /api/stt and return response JSON."""
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{config.STT_URL}/api/stt",
            files={"file": (os.path.basename(filepath), f)},
            timeout=config.STT_REQUEST_TIMEOUT_SEC,
        )
    resp.raise_for_status()
    return resp.json()


def make_wav_from_ogg(ogg_path: str) -> str:
    """Transcode to a temp WAV and return its path (caller unlinks)."""
    fd, name = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        subprocess.check_output(
            [
                "ffmpeg",
                "-y",
                "-i",
                ogg_path,
                "-ac",
                "1",
                "-ar",
                "16000",
                name,
            ],
            stderr=subprocess.STDOUT,
            timeout=120,
        )
    except Exception as exc:
        if os.path.isfile(name):
            os.unlink(name)
        raise exc
    return name


def transcribe_segment_path(path: str) -> Dict[str, Any]:
    """Transcribe file; when STT_USE_WAV, send WAV; else retry ogg with WAV on failure."""
    tmp: str | None = None
    if config.STT_USE_WAV and path.lower().endswith(".ogg"):
        tmp = make_wav_from_ogg(path)
        try:
            return transcribe_file(tmp)
        finally:
            if tmp and os.path.isfile(tmp):
                os.unlink(tmp)

    try:
        return transcribe_file(path)
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        relog = tmp is None and path.lower().endswith(".ogg") and status in (
            400,
            415,
            422,
            500,
        )
        if not relog:
            raise
        body = (e.response.text or "") if e.response is not None else ""
        logger.warning(
            f"STT rejected Ogg HTTP {status}, retrying WAV. Body: {body[:500]}"
        )
        w = make_wav_from_ogg(path)
        try:
            return transcribe_file(w)
        finally:
            if os.path.isfile(w):
                os.unlink(w)


def main() -> None:
    pass


if __name__ == "__main__":
    main()
