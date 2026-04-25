#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Peewee ORM models for the voice recorder."""

import os
from datetime import datetime
from pathlib import Path

import pytz
from peewee import (
    BigAutoField,
    CharField,
    DateTimeField,
    DoubleField,
    IntegerField,
    Model,
    TextField,
)

# Local imports
from api.db import SQLITE

TIMEZONE = pytz.timezone(os.getenv("TZ", "UTC"))


def now_tz() -> datetime:
    return datetime.now(TIMEZONE)


class Segment(Model):
    """A single on-disk Ogg segment with optional STT transcript."""

    id = BigAutoField(primary_key=True)
    created_at = DateTimeField(default=now_tz)
    updated_at = DateTimeField(default=now_tz)
    removed_at = DateTimeField(null=True)

    file_path = CharField(max_length=1024, unique=True)
    file_name = CharField(max_length=512)
    segment_start = DateTimeField()
    segment_end = DateTimeField()

    bytes_size = IntegerField()
    duration_sec = DoubleField(null=True)

    transcript = TextField(null=True)
    stt_status = CharField(max_length=32, default="pending")
    stt_error = TextField(null=True)
    stt_at = DateTimeField(null=True)

    class Meta:
        table_name = "segments"
        database = SQLITE

    def save(self, *args, **kwargs):
        self.updated_at = now_tz()
        return super().save(*args, **kwargs)


def create_tables() -> None:
    """Create Peewee tables if they do not exist."""
    db_name = SQLITE.database
    if db_name and not str(db_name).startswith(":"):
        Path(db_name).parent.mkdir(parents=True, exist_ok=True)
    with SQLITE:
        SQLITE.create_tables([Segment], safe=True)


def main() -> None:
    pass


if __name__ == "__main__":
    main()
