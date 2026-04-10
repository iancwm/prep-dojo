from __future__ import annotations

from types import SimpleNamespace

from fastapi import HTTPException

from app.core import observability


def test_generate_request_id_uses_compact_hex_value(monkeypatch) -> None:
    monkeypatch.setattr(observability, "uuid4", lambda: SimpleNamespace(hex="abc123"))

    assert observability.generate_request_id() == "abc123"


def test_finish_request_timer_measures_elapsed_time() -> None:
    timing = observability.finish_request_timer(1_000, 1_500_000)

    assert timing.started_at_ns == 1_000
    assert timing.finished_at_ns == 1_500_000
    assert timing.duration_ns == 1_499_000
    assert timing.duration_ms == 1.499


def test_build_request_log_payload_normalizes_shape_and_merges_extra() -> None:
    timing = observability.finish_request_timer(100, 2_000_100)

    payload = observability.build_request_log_payload(
        request_id="req-1",
        method="post",
        path="/api/v1/authored/questions",
        status_code=201,
        timing=timing,
        client_ip="127.0.0.1",
        query_string="source=demo",
        user_role=None,
        extra={"route_name": "create_authored_question"},
    )

    assert payload == {
        "event": "request",
        "request_id": "req-1",
        "method": "POST",
        "path": "/api/v1/authored/questions",
        "status_code": 201,
        "duration_ns": 2_000_000,
        "duration_ms": 2.0,
        "client_ip": "127.0.0.1",
        "query_string": "source=demo",
        "route_name": "create_authored_question",
    }


def test_build_exception_log_payload_captures_http_exception_context() -> None:
    timing = observability.finish_request_timer(10, 35)
    error = HTTPException(status_code=404, detail="Unknown authored question.")

    payload = observability.build_exception_log_payload(
        request_id="req-2",
        exception=error,
        method="get",
        path="/api/v1/authored/questions/123",
        timing=timing,
        extra={"endpoint": "question_lookup"},
    )

    assert payload == {
        "event": "exception",
        "request_id": "req-2",
        "exception_type": "HTTPException",
        "message": "Unknown authored question.",
        "method": "GET",
        "path": "/api/v1/authored/questions/123",
        "duration_ns": 25,
        "duration_ms": 0.0,
        "http_status_code": 404,
        "endpoint": "question_lookup",
    }


def test_build_exception_log_payload_handles_generic_exception() -> None:
    payload = observability.build_exception_log_payload(
        request_id="req-3",
        exception=ValueError("bad input"),
    )

    assert payload == {
        "event": "exception",
        "request_id": "req-3",
        "exception_type": "ValueError",
        "message": "bad input",
    }
