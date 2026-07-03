from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> tuple[int, str]:
    ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    iso_time = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    return ts_ms, iso_time


def ok_response(
    *,
    query: dict[str, Any],
    data: dict[str, Any],
    stats: dict[str, Any] | None = None,
    summary: str,
    highlights: list[str],
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ts_ms, iso_time = _now()
    return {
        "ok": True,
        "summary": summary,
        "highlights": highlights,
        "query": query,
        "ts_ms": ts_ms,
        "iso_time": iso_time,
        "data": data,
        "stats": stats or {},
        "meta": meta or {},
        "error": None,
    }


def error_response(
    *,
    query: dict[str, Any],
    code: str,
    message: str,
    context: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ts_ms, iso_time = _now()
    return {
        "ok": False,
        "summary": message,
        "highlights": [f"error_code={code}"],
        "query": query,
        "ts_ms": ts_ms,
        "iso_time": iso_time,
        "data": {},
        "stats": {},
        "meta": meta or {},
        "error": {
            "code": code,
            "message": message,
            "context": context or {"method": None, "retryable": False},
        },
    }
