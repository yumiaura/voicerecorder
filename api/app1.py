#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flask API: recording metadata, Ogg stream with Range, static UI path."""

import logging
import os
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

# Project root for imports and static files
_PROJ = Path(__file__).resolve().parent.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))

import werkzeug
from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, request, send_file, send_from_directory
from peewee import DoesNotExist, fn
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from marshmallow import ValidationError

# Local imports
import config
from api import serializers
from api.db import SQLITE
from api.local_auth import check_password, issue_access_token, token_ok
from api.models import Segment, create_tables
from api.serializers import segment_serializer
from api.validators import LoginBodySchema, SegmentsFilterSchema

load_dotenv(find_dotenv())

LOGGING = {
    "handlers": [logging.StreamHandler()],
    "format": "%(asctime)s.%(msecs)03d [%(levelname)s]: (%(name)s) %(message)s",
    "level": logging.INFO,
    "datefmt": "%Y-%m-%d %H:%M:%S",
}
logging.basicConfig(**LOGGING)
logger = logging.getLogger(__name__)

TRUE_VALUES = ("1", "true", "yes", "on", "enabled")
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in TRUE_VALUES


class JSONProvider(DefaultJSONProvider):
    """Custom JSON for datetime objects."""

    def default(self, o):
        if isinstance(o, date) and not isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, datetime):
            s = serializers.format_datetime(o)
            if s is not None:
                return s
        return super().default(o)


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=None,
    )
    app.json = JSONProvider(app)
    app.url_map.strict_slashes = False
    app.config["SECRET_KEY"] = config.SECRET_KEY
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": "*",
                "allow_headers": [
                    "Content-Type",
                    "Authorization",
                ],
            },
        },
    )

    @app.before_request
    def before_request():
        if SQLITE.is_closed():
            SQLITE.connect(reuse_if_open=True)
        if request.method == "OPTIONS":
            return None
        if request.path.startswith("/api/") and not (
            request.path == "/api/auth/login" and request.method == "POST"
        ):
            if not token_ok(request):
                return (
                    jsonify(
                        {
                            "error": "Unauthorized",
                            "message": "Missing or invalid access token",
                        }
                    ),
                    401,
                )
        return None

    @app.after_request
    def after_request(resp):
        logger.info(
            f"{request.method} {request.path}: {resp.status_code} {resp.status}"
        )
        return resp

    @app.teardown_request
    def close_db(_exc):
        if not SQLITE.is_closed():
            SQLITE.close()

    @app.route("/api/auth/login", methods=["POST"])
    def auth_login():
        data = request.get_json(silent=True) or {}
        err = LoginBodySchema().validate(data)
        if err:
            return jsonify({"error": err}), 400
        f = LoginBodySchema().load(data)
        u = f.get("username", "")
        p = f.get("password", "")
        if not check_password(str(u), str(p)):
            return (
                jsonify(
                    {
                        "error": "Invalid credentials",
                        "message": "Invalid username or password",
                    }
                ),
                401,
            )
        t = issue_access_token()
        return (
            jsonify(
                {
                    "access_token": t,
                    "token_type": "Bearer",
                    "expires_in": int(config.AUTH_JWT_HOURS * 3600),
                }
            ),
            200,
        )

    @app.route("/api/days", methods=["GET"])
    def list_days():
        rows = (
            Segment.select(
                fn.strftime("%Y-%m-%d", Segment.segment_start).alias("d")
            )
            .where(Segment.removed_at.is_null())
        )
        day_set = set()
        for row in rows:
            if row.d:
                day_set.add(row.d)
        ordered = sorted(day_set)
        return jsonify({"items": ordered}), 200

    @app.route("/api/segments", methods=["GET"])
    def list_segments():
        err = SegmentsFilterSchema().validate(request.args)
        if err:
            return jsonify({"error": err}), 400
        f = SegmentsFilterSchema().load(request.args)
        day_str = f.get("day")
        q = (
            Segment.select()
            .where(
                (Segment.removed_at.is_null())
                & (
                    fn.strftime("%Y-%m-%d", Segment.segment_start)
                    == day_str
                )
            )
            .order_by(Segment.segment_start)
        )
        items = [segment_serializer(s) for s in q]
        return jsonify({"items": items, "date": day_str}), 200

    @app.route("/api/segments/<int:segment_id>", methods=["GET"])
    def get_segment(segment_id: int):
        try:
            s = Segment.get_by_id(segment_id)
        except DoesNotExist:
            return jsonify({"error": "Not Found", "message": "Segment not found"}), 404
        if s.removed_at is not None:
            return jsonify({"error": "Not Found", "message": "Segment not found"}), 404
        return jsonify(segment_serializer(s)), 200

    @app.route("/api/stream/<int:segment_id>", methods=["GET"])
    def stream_segment(segment_id: int):
        try:
            s = Segment.get_by_id(segment_id)
        except DoesNotExist:
            return jsonify({"error": "Not Found", "message": "Segment not found"}), 404
        if s.removed_at is not None:
            return jsonify({"error": "Not Found", "message": "Segment not found"}), 404
        path = Path(s.file_path)
        if not path.is_file():
            return jsonify({"error": "NotFound", "message": "File missing on disk"}), 404
        return send_file(
            path,
            mimetype="audio/ogg",
            as_attachment=False,
            conditional=True,
        )

    www_dir = str(_PROJ / "www" / "src")

    @app.route("/")
    def index_page():
        resp = send_from_directory(www_dir, "index.html")
        resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp

    @app.route("/<path:rel>")
    def static_www(rel: str):
        base = (_PROJ / "www" / "src").resolve()
        target = (base / rel).resolve()
        if not str(target).startswith(str(base)):
            return jsonify({"error": "NotFound"}), 404
        if not target.is_file():
            return index_page()
        resp = send_file(target, conditional=True)
        if rel.endswith((".js", ".vue", ".html")):
            resp.headers["Cache-Control"] = "no-store, max-age=0"
        return resp

    @app.errorhandler(400)
    def bad_request(err):
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": str(err),
                }
            ),
            400,
        )

    @app.errorhandler(404)
    def not_found(err):
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": str(err),
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed(err):
        return (
            jsonify(
                {
                    "error": "Method Not Allowed",
                    "message": str(err),
                }
            ),
            405,
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"error": err.messages}), 400

    @app.errorhandler(Exception)
    def handle_exception(exc):
        if isinstance(exc, werkzeug.exceptions.NotFound):
            return jsonify({"error": "NotFound"}), 404
        if isinstance(exc, werkzeug.exceptions.MethodNotAllowed):
            return (
                jsonify(
                    {
                        "error": "Method Not Allowed",
                        "message": str(exc),
                    }
                ),
                405,
            )
        logger.error(f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}")
        return (
            jsonify({"error": f"{type(exc).__name__}", "message": str(exc)}),
            500,
        )

    return app


app = create_app()


def main() -> None:
    create_tables()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, threaded=True)


if __name__ == "__main__":
    main()
