#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite connection (Peewee)."""

import config
from peewee import SqliteDatabase

SQLITE = SqliteDatabase(
    config.SQLITE_PATH,
    pragmas={"journal_mode": "wal", "foreign_keys": 1},
)
