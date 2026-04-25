#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Marshmallow request validation schemas."""

from marshmallow import Schema, fields, validate

DATE_RX = r"^\d{4}-\d{2}-\d{2}$"


class LoginBodySchema(Schema):
    """JSON body for POST /api/auth/login."""

    username = fields.Str(
        required=True, validate=validate.Length(min=1, max=256)
    )
    password = fields.Str(
        required=True, validate=validate.Length(min=1, max=256)
    )


class SegmentsFilterSchema(Schema):
    """Query-string for GET /api/segments."""

    day = fields.Str(
        required=True,
        validate=validate.Regexp(DATE_RX),
    )


def main() -> None:
    pass


if __name__ == "__main__":
    main()
