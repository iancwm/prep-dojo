from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns
from typing import Any
from uuid import uuid4

from fastapi import HTTPException


def generate_request_id() -> str:
    """Return a compact, opaque request identifier."""
    return uuid4().hex


def start_request_timer() -> int:
    """Capture a monotonic timestamp for request timing."""
    return perf_counter_ns()


@dataclass(frozen=True)
class RequestTiming:
    started_at_ns: int
    finished_at_ns: int

    @property
    def duration_ns(self) -> int:
        return self.finished_at_ns - self.started_at_ns

    @property
    def duration_ms(self) -> float:
        return round(self.duration_ns / 1_000_000, 3)


def finish_request_timer(started_at_ns: int, finished_at_ns: int | None = None) -> RequestTiming:
    """Return a finished timing record for a request."""
    if finished_at_ns is None:
        finished_at_ns = perf_counter_ns()
    return RequestTiming(started_at_ns=started_at_ns, finished_at_ns=finished_at_ns)


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def build_request_log_payload(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    timing: RequestTiming,
    client_ip: str | None = None,
    query_string: str | None = None,
    user_role: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": "request",
        "request_id": request_id,
        "method": method.upper(),
        "path": path,
        "status_code": status_code,
        "duration_ns": timing.duration_ns,
        "duration_ms": timing.duration_ms,
        "client_ip": client_ip,
        "query_string": query_string,
        "user_role": user_role,
    }
    if extra:
        payload.update(extra)
    return _clean_payload(payload)


def _exception_detail(exception: Exception) -> str:
    if isinstance(exception, HTTPException):
        detail = exception.detail
        if isinstance(detail, str):
            return detail
        return str(detail)
    return str(exception)


def build_exception_log_payload(
    *,
    request_id: str,
    exception: Exception,
    method: str | None = None,
    path: str | None = None,
    status_code: int | None = None,
    timing: RequestTiming | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event": "exception",
        "request_id": request_id,
        "exception_type": exception.__class__.__name__,
        "message": _exception_detail(exception),
        "method": method.upper() if method is not None else None,
        "path": path,
        "status_code": status_code,
        "duration_ns": timing.duration_ns if timing is not None else None,
        "duration_ms": timing.duration_ms if timing is not None else None,
    }
    if isinstance(exception, HTTPException):
        payload["http_status_code"] = exception.status_code
    if extra:
        payload.update(extra)
    return _clean_payload(payload)
