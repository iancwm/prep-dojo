from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import fastapi.testclient as fastapi_testclient
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.auth import ROLE_HEADER, get_request_auth_context, require_mentor_like_role
from app.main import (
    archive_authored_concept,
    archive_authored_topic,
    complete_practice_session_route,
    create_authored_concept,
    create_authored_question,
    create_authored_topic,
    create_practice_session,
    get_authored_question,
    get_practice_session,
    get_reference_question,
    get_valuation_reference_module,
    get_valuation_reference_progress,
    healthcheck,
    list_authored_concepts,
    list_assessment_modes,
    list_authored_questions,
    list_authored_topics,
    list_practice_sessions,
    list_reference_questions,
    start_practice_session_route,
    submit_authored_question_attempt,
    submit_reference_question_attempt,
    submit_valuation_reference_attempt,
    update_authored_question_status,
    update_authored_question,
    update_authored_concept,
    update_authored_topic,
)
from app.schemas.domain import (
    AuthoredQuestionBundleCreate,
    AuthoredQuestionBundleUpdate,
    ConceptListFilters,
    ConceptCreate,
    ConceptUpdate,
    ContentStatusTransitionRequest,
    PracticeSessionCreate,
    PracticeSessionListFilters,
    PracticeSessionTransitionRequest,
    StudentAttemptCreate,
    TopicListFilters,
    TopicCreate,
    TopicUpdate,
)
from app.db.session import get_session


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _LocalResponse:
    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body, default=str)

    def json(self) -> Any:
        return self._body


@contextmanager
def _session_from_app(app):
    session_factory = app.dependency_overrides.get(get_session, get_session)
    session_gen = session_factory()
    session = next(session_gen)
    try:
        yield session
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


class InProcessClient:
    __test__ = False

    def __init__(self, app, *args, **kwargs):
        self.app = app

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, path: str, **kwargs) -> _LocalResponse:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> _LocalResponse:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> _LocalResponse:
        return self._request("PUT", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs) -> _LocalResponse:
        payload = kwargs.get("json")
        headers = kwargs.get("headers") or {}

        try:
            if method == "GET" and path == "/healthz":
                return _LocalResponse(200, healthcheck())
            if method == "GET" and path == "/api/v1/reference/assessment-modes":
                return _LocalResponse(200, list_assessment_modes())
            if method == "GET" and path == "/api/v1/reference/modules/valuation-enterprise-value":
                return _LocalResponse(200, get_valuation_reference_module())
            if method == "GET" and path == "/api/v1/reference/modules/valuation-enterprise-value/progress":
                return _LocalResponse(200, get_valuation_reference_progress())
            if method == "GET" and path == "/api/v1/reference/questions":
                return _LocalResponse(200, list_reference_questions())
            if method == "POST" and path == "/api/v1/reference/modules/valuation-enterprise-value/submit":
                attempt = StudentAttemptCreate.model_validate(payload)
                with _session_from_app(self.app) as session:
                    result = submit_valuation_reference_attempt(attempt, session=session)
                return _LocalResponse(200, result)
            if method == "GET" and path.startswith("/api/v1/reference/questions/"):
                question_external_id = path.rsplit("/", 1)[-1]
                with _session_from_app(self.app) as session:
                    result = get_reference_question(question_external_id, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/reference/questions/") and path.endswith("/submit"):
                question_external_id = path.split("/")[5]
                attempt = StudentAttemptCreate.model_validate(payload)
                with _session_from_app(self.app) as session:
                    result = submit_reference_question_attempt(
                        question_external_id,
                        attempt,
                        session=session,
                    )
                return _LocalResponse(200, result)
            if method == "POST" and path == "/api/v1/practice-sessions":
                create_payload = PracticeSessionCreate.model_validate(payload)
                with _session_from_app(self.app) as session:
                    result = create_practice_session(create_payload, session=session)
                return _LocalResponse(201, result)
            if method == "GET" and path == "/api/v1/practice-sessions":
                list_filters = PracticeSessionListFilters.model_validate(
                    {
                        "status": kwargs.get("params", {}).get("status"),
                        "source": kwargs.get("params", {}).get("source"),
                        "started_after": kwargs.get("params", {}).get("started_after"),
                        "started_before": kwargs.get("params", {}).get("started_before"),
                        "current_question_id": kwargs.get("params", {}).get("current_question_id"),
                        "has_remaining": kwargs.get("params", {}).get("has_remaining"),
                    }
                )
                with _session_from_app(self.app) as session:
                    result = list_practice_sessions(
                        status=list_filters.status,
                        source=list_filters.source,
                        started_after=list_filters.started_after,
                        started_before=list_filters.started_before,
                        current_question_id=list_filters.current_question_id,
                        has_remaining=list_filters.has_remaining,
                        session=session,
                    )
                return _LocalResponse(200, result)
            if method == "GET" and path.startswith("/api/v1/practice-sessions/"):
                session_id = path.rsplit("/", 1)[-1]
                with _session_from_app(self.app) as session:
                    result = get_practice_session(session_id, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/practice-sessions/") and path.endswith("/start"):
                session_id = path.split("/")[4]
                transition_payload = PracticeSessionTransitionRequest.model_validate(payload)
                with _session_from_app(self.app) as session:
                    result = start_practice_session_route(session_id, transition_payload, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/practice-sessions/") and path.endswith("/complete"):
                session_id = path.split("/")[4]
                transition_payload = PracticeSessionTransitionRequest.model_validate(payload)
                with _session_from_app(self.app) as session:
                    result = complete_practice_session_route(session_id, transition_payload, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path == "/api/v1/authored/questions":
                create_payload = AuthoredQuestionBundleCreate.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = create_authored_question(create_payload, session=session)
                return _LocalResponse(201, result)
            if method == "POST" and path == "/api/v1/authored/topics":
                create_payload = TopicCreate.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = create_authored_topic(create_payload, session=session)
                return _LocalResponse(201, result)
            if method == "GET" and path == "/api/v1/authored/topics":
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                list_filters = TopicListFilters.model_validate(
                    {
                        "status": kwargs.get("params", {}).get("status"),
                        "include_archived": kwargs.get("params", {}).get("include_archived", False),
                    }
                )
                with _session_from_app(self.app) as session:
                    result = list_authored_topics(
                        status=list_filters.status,
                        include_archived=list_filters.include_archived,
                        session=session,
                    )
                return _LocalResponse(200, result)
            if method == "PUT" and path.startswith("/api/v1/authored/topics/"):
                topic_slug = path.rsplit("/", 1)[-1]
                update_payload = TopicUpdate.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = update_authored_topic(topic_slug, update_payload, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/authored/topics/") and path.endswith("/archive"):
                topic_slug = path.split("/")[5]
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = archive_authored_topic(topic_slug, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path == "/api/v1/authored/concepts":
                create_payload = ConceptCreate.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = create_authored_concept(create_payload, session=session)
                return _LocalResponse(201, result)
            if method == "GET" and path.startswith("/api/v1/authored/concepts"):
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                list_filters = ConceptListFilters.model_validate(
                    {
                        "topic_slug": kwargs.get("params", {}).get("topic_slug"),
                        "status": kwargs.get("params", {}).get("status"),
                        "include_archived": kwargs.get("params", {}).get("include_archived", False),
                    }
                )
                with _session_from_app(self.app) as session:
                    result = list_authored_concepts(
                        topic_slug=list_filters.topic_slug,
                        status=list_filters.status,
                        include_archived=list_filters.include_archived,
                        session=session,
                    )
                return _LocalResponse(200, result)
            if method == "PUT" and path.startswith("/api/v1/authored/concepts/"):
                concept_slug = path.rsplit("/", 1)[-1]
                update_payload = ConceptUpdate.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = update_authored_concept(concept_slug, update_payload, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/authored/concepts/") and path.endswith("/archive"):
                concept_slug = path.split("/")[5]
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = archive_authored_concept(concept_slug, session=session)
                return _LocalResponse(200, result)
            if method == "GET" and path == "/api/v1/authored/questions":
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = list_authored_questions(
                        status_filter=kwargs.get("params", {}).get("status_filter"),
                        topic_slug=kwargs.get("params", {}).get("topic_slug"),
                        concept_slug=kwargs.get("params", {}).get("concept_slug"),
                        session=session,
                    )
                return _LocalResponse(200, result)
            if method == "GET" and path.startswith("/api/v1/authored/questions/") and not path.endswith("/status"):
                question_id = path.rsplit("/", 1)[-1]
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = get_authored_question(question_id, session=session)
                return _LocalResponse(200, result)
            if method == "PUT" and path.startswith("/api/v1/authored/questions/"):
                question_id = path.rsplit("/", 1)[-1]
                update_payload = AuthoredQuestionBundleUpdate.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = update_authored_question(question_id, update_payload, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/authored/questions/") and path.endswith("/status"):
                question_id = path.split("/")[5]
                transition_payload = ContentStatusTransitionRequest.model_validate(payload)
                require_mentor_like_role(get_request_auth_context(headers.get(ROLE_HEADER)))
                with _session_from_app(self.app) as session:
                    result = update_authored_question_status(question_id, transition_payload, session=session)
                return _LocalResponse(200, result)
            if method == "POST" and path.startswith("/api/v1/authored/questions/") and path.endswith("/submit"):
                question_id = path.split("/")[5]
                attempt = StudentAttemptCreate.model_validate(payload)
                with _session_from_app(self.app) as session:
                    result = submit_authored_question_attempt(question_id, attempt, session=session)
                return _LocalResponse(200, result)
        except ValidationError as exc:
            return _LocalResponse(422, {"detail": exc.errors()})
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, (dict, list)) else {"detail": exc.detail}
            return _LocalResponse(exc.status_code, detail)

        raise AssertionError(f"Unhandled {method} {path}")


fastapi_testclient.TestClient = InProcessClient
