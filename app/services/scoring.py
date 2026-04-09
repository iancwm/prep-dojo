from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

from app.core.enums import MasteryBand, ScoringMethod
from app.db.models import CommonMistake, ExpectedAnswer, Question, Rubric
from app.schemas.domain import CriterionScore, FeedbackResult, RubricCriterion, ScoreResult, StudentAttemptCreate
from app.seeds.reference_data import (
    PRIMARY_REFERENCE_QUESTION_ID,
    SECONDARY_REFERENCE_QUESTION_ID,
    get_reference_follow_up_question_bundle,
    get_reference_module,
)

REFERENCE_QUESTION_ID = PRIMARY_REFERENCE_QUESTION_ID


def score_reference_attempt(attempt: StudentAttemptCreate) -> tuple[ScoreResult, FeedbackResult]:
    if attempt.question_id == PRIMARY_REFERENCE_QUESTION_ID:
        bundle = get_reference_module().question_bundle
    elif attempt.question_id == SECONDARY_REFERENCE_QUESTION_ID:
        bundle = get_reference_follow_up_question_bundle()
    else:
        raise HTTPException(status_code=404, detail="Unknown reference question.")

    return score_attempt_from_contract(
        attempt=attempt,
        rubric_criteria=bundle.rubric.criteria,
        rubric_thresholds=bundle.rubric.thresholds,
        expected_key_points=bundle.expected_answer.key_points,
        expected_outline=bundle.expected_answer.answer_outline,
        common_mistakes=[item.mistake_text for item in bundle.common_mistakes],
    )


def score_attempt_for_question(
    attempt: StudentAttemptCreate,
    *,
    question: Question,
    rubric: Rubric,
    expected_answer: ExpectedAnswer,
    common_mistakes: list[CommonMistake],
) -> tuple[ScoreResult, FeedbackResult]:
    valid_identifiers = {str(question.id)}
    if question.external_id is not None:
        valid_identifiers.add(question.external_id)

    if attempt.question_id not in valid_identifiers:
        raise HTTPException(status_code=404, detail="Question id does not match stored question.")

    return score_attempt_from_contract(
        attempt=attempt,
        question_payload=question.payload_json,
        rubric_criteria=[RubricCriterion.model_validate(item) for item in rubric.criteria_json],
        rubric_thresholds=rubric.thresholds_json,
        expected_key_points=expected_answer.key_points_json,
        expected_outline=expected_answer.answer_outline_json,
        common_mistakes=[item.mistake_text for item in common_mistakes],
    )


def score_attempt_from_contract(
    *,
    attempt: StudentAttemptCreate,
    question_payload: dict[str, Any] | None = None,
    rubric_criteria: list[RubricCriterion],
    rubric_thresholds: list,
    expected_key_points: list[str],
    expected_outline: list[str],
    common_mistakes: list[str],
) -> tuple[ScoreResult, FeedbackResult]:
    question_type = question_payload.get("question_type") if question_payload else None
    if attempt.response.response_type == "multiple_choice":
        return _score_multiple_choice_response(
            attempt=attempt,
            question_payload=question_payload,
            rubric_criteria=rubric_criteria,
            rubric_thresholds=rubric_thresholds,
        )
    if attempt.response.response_type == "oral_transcript":
        if question_type not in {None, "oral_recall"}:
            raise HTTPException(status_code=400, detail="Question does not accept oral transcript responses.")
        return _score_textual_response(
            content=attempt.response.transcript.strip(),
            rubric_criteria=rubric_criteria,
            rubric_thresholds=rubric_thresholds,
            expected_key_points=expected_key_points,
            expected_outline=expected_outline,
            common_mistakes=common_mistakes,
            scoring_method=ScoringMethod.HYBRID,
        )
    if attempt.response.response_type != "free_text":
        raise HTTPException(status_code=400, detail="Unsupported response type.")
    if question_type == "mcq_single":
        raise HTTPException(status_code=400, detail="Question does not accept free-text responses.")

    return _score_textual_response(
        content=attempt.response.content.strip(),
        rubric_criteria=rubric_criteria,
        rubric_thresholds=rubric_thresholds,
        expected_key_points=expected_key_points,
        expected_outline=expected_outline,
        common_mistakes=common_mistakes,
        scoring_method=ScoringMethod.HYBRID,
    )


def _score_textual_response(
    *,
    content: str,
    rubric_criteria: list[RubricCriterion],
    rubric_thresholds: list,
    expected_key_points: list[str],
    expected_outline: list[str],
    common_mistakes: list[str],
    scoring_method: ScoringMethod,
) -> tuple[ScoreResult, FeedbackResult]:
    lowered = _normalize_text(content)

    criterion_scores = [
        _score_named_criterion(
            criterion=criterion,
            lowered=lowered,
            raw_content=content,
            expected_key_points=expected_key_points,
            expected_outline=expected_outline,
            common_mistakes=common_mistakes,
        )
        for criterion in rubric_criteria
    ]
    overall_score = _calculate_overall_score(criterion_scores, rubric_criteria)
    mastery_band = _resolve_mastery_band(overall_score, rubric_thresholds)
    feedback = _build_feedback(
        lowered=lowered,
        criterion_scores=criterion_scores,
        mastery_band=mastery_band,
        rubric_criteria=rubric_criteria,
        expected_key_points=expected_key_points,
    )

    score = ScoreResult(
        overall_score=overall_score,
        mastery_band=mastery_band,
        scoring_method=scoring_method,
        criterion_scores=criterion_scores,
    )
    return score, feedback


def _score_multiple_choice_response(
    *,
    attempt: StudentAttemptCreate,
    question_payload: dict[str, Any] | None,
    rubric_criteria: list[RubricCriterion],
    rubric_thresholds: list,
) -> tuple[ScoreResult, FeedbackResult]:
    if question_payload is None or question_payload.get("question_type") != "mcq_single":
        raise HTTPException(status_code=400, detail="Question does not accept multiple-choice responses.")

    correct_option_id = question_payload.get("correct_option_id")
    explanation = question_payload.get("explanation", "")
    selected_option_id = attempt.response.selected_option_id
    is_correct = selected_option_id == correct_option_id

    criterion_scores = []
    for criterion in rubric_criteria:
        score = criterion.max_score if is_correct else 0
        note = "Selected the correct option." if is_correct else "Selected the wrong option."
        criterion_scores.append(
            CriterionScore(
                criterion_name=criterion.name,
                score=score,
                max_score=criterion.max_score,
                notes=note,
            )
        )

    overall_score = _calculate_overall_score(criterion_scores, rubric_criteria)
    mastery_band = _resolve_mastery_band(overall_score, rubric_thresholds)
    feedback = _build_multiple_choice_feedback(
        is_correct=is_correct,
        explanation=explanation,
        selected_option_id=selected_option_id,
        correct_option_id=correct_option_id,
    )
    score = ScoreResult(
        overall_score=overall_score,
        mastery_band=mastery_band,
        scoring_method=ScoringMethod.AUTOMATIC,
        criterion_scores=criterion_scores,
    )
    return score, feedback


def _score_named_criterion(
    *,
    criterion: RubricCriterion,
    lowered: str,
    raw_content: str,
    expected_key_points: list[str],
    expected_outline: list[str],
    common_mistakes: list[str],
) -> CriterionScore:
    criterion_name = criterion.name.lower()
    if criterion_name == "clarity":
        return _score_clarity(raw_content, criterion.max_score)
    if criterion_name == "recall":
        return _score_recall_like(criterion, lowered, expected_key_points)
    if criterion_name == "reasoning":
        return _score_reasoning_like(criterion, lowered, expected_outline)
    if criterion_name == "application":
        return _score_application_like(criterion, lowered, expected_key_points)

    return _score_semantic_criterion(
        criterion=criterion,
        lowered=lowered,
        expected_key_points=expected_key_points,
        expected_outline=expected_outline,
        common_mistakes=common_mistakes,
    )


def _score_recall_like(
    criterion: RubricCriterion,
    lowered: str,
    expected_key_points: list[str],
) -> CriterionScore:
    fragment_hits = _fragment_hits(lowered, list(criterion.strong_response_fragments) + expected_key_points[:2])
    definition_hits = 0
    if "ev" in lowered or "enterprise value" in lowered:
        definition_hits += 1
    if "equityvalue" in lowered or "shareholder" in lowered or "market cap" in lowered:
        definition_hits += 1

    if definition_hits == 2 and fragment_hits >= 1:
        score = criterion.max_score
        note = "Recall is fully supported by the answer."
    elif definition_hits >= 1:
        score = max(criterion.max_score - 1, 1)
        note = "Recall is present but could be sharper."
    else:
        score = 0
        note = "Recall is missing from the answer."
    return CriterionScore(criterion_name=criterion.name, score=score, max_score=criterion.max_score, notes=note)


def _score_reasoning_like(
    criterion: RubricCriterion,
    lowered: str,
    expected_outline: list[str],
) -> CriterionScore:
    fragment_hits = _fragment_hits(lowered, list(criterion.strong_response_fragments) + expected_outline)
    reasoning_signals = [
        "because",
        "capital structure",
        "debt",
        "cash",
        "leverage",
        "operating comparison",
        "operating comparisons",
        "compare",
        "comparison",
        "normalize",
        "normalizes",
    ]
    signal_hits = sum(1 for signal in reasoning_signals if signal in lowered)

    if signal_hits >= 3 or (signal_hits >= 2 and fragment_hits >= 1):
        score = criterion.max_score
        note = "Reasoning is fully supported by the answer."
    elif signal_hits >= 1 or fragment_hits >= 1:
        score = max(criterion.max_score - 1, 1)
        note = "Reasoning is present but could be sharper."
    else:
        score = 0
        note = "Reasoning is missing from the answer."
    return CriterionScore(criterion_name=criterion.name, score=score, max_score=criterion.max_score, notes=note)


def _score_application_like(
    criterion: RubricCriterion,
    lowered: str,
    expected_key_points: list[str],
) -> CriterionScore:
    fragment_hits = _fragment_hits(lowered, list(criterion.strong_response_fragments) + expected_key_points)
    application_signals = [
        "ev / ebitda",
        "p / e",
        "per-share",
        "interview",
        "shareholder perspective",
        "metric",
        "metrics",
        "compare companies",
    ]
    signal_hits = sum(1 for signal in application_signals if signal in lowered)

    if signal_hits >= 2 or fragment_hits >= 2:
        score = criterion.max_score
        note = "Application is fully supported by the answer."
    elif signal_hits >= 1 or fragment_hits >= 1:
        score = max(criterion.max_score - 1, 1)
        note = "Application is present but could be sharper."
    else:
        score = 0
        note = "Application is missing from the answer."
    return CriterionScore(criterion_name=criterion.name, score=score, max_score=criterion.max_score, notes=note)


def _score_semantic_criterion(
    *,
    criterion: RubricCriterion,
    lowered: str,
    expected_key_points: list[str],
    expected_outline: list[str],
    common_mistakes: list[str],
) -> CriterionScore:
    fragments = list(criterion.strong_response_fragments)
    if criterion.name.lower() == "recall":
        fragments.extend(expected_key_points[:2])
    elif criterion.name.lower() == "reasoning":
        fragments.extend(expected_outline)
    elif criterion.name.lower() == "application":
        fragments.extend(expected_key_points)

    total = max(len(fragments), 1)
    matched = sum(1 for fragment in fragments if _matches_fragment(lowered, fragment))
    ratio = matched / total
    score = round(criterion.max_score * min(ratio * 1.35, 1.0))

    penalty = sum(1 for item in criterion.failure_signals if _matches_fragment(lowered, item))
    penalty += sum(1 for item in common_mistakes if _matches_fragment(lowered, item))
    score = max(score - min(penalty, 1), 0)

    if score == criterion.max_score:
        note = f"{criterion.name.capitalize()} is fully supported by the answer."
    elif score >= max(1, criterion.max_score - 1):
        note = f"{criterion.name.capitalize()} is present but could be sharper."
    elif score > 0:
        note = f"{criterion.name.capitalize()} is hinted at, but still incomplete."
    else:
        note = f"{criterion.name.capitalize()} is missing from the answer."

    return CriterionScore(criterion_name=criterion.name, score=score, max_score=criterion.max_score, notes=note)


def _score_clarity(content: str, max_score: int) -> CriterionScore:
    word_count = len(content.split())
    has_structure = any(token in content for token in [".", ";", ":"])
    if word_count >= 35 and has_structure:
        score = max_score
        note = "The answer is developed enough to sound deliberate under pressure."
    elif word_count >= 20:
        score = max(max_score - 1, 1)
        note = "The answer is concise and usable, but could be more structured."
    elif word_count >= 10:
        score = max(max_score - 2, 1)
        note = "The answer is brief and likely too compressed in a live interview."
    else:
        score = 0
        note = "The answer is too thin to be credible."
    return CriterionScore(criterion_name="clarity", score=score, max_score=max_score, notes=note)


def _calculate_overall_score(
    criterion_scores: list[CriterionScore],
    rubric_criteria: list[RubricCriterion],
) -> float:
    weighted_total = 0.0
    for criterion_score, rubric_criterion in zip(criterion_scores, rubric_criteria, strict=True):
        weighted_total += (criterion_score.score / criterion_score.max_score) * rubric_criterion.weight
    return round(weighted_total * 100, 1)


def _resolve_mastery_band(overall_score: float, thresholds: list) -> MasteryBand:
    winning_band = MasteryBand.NEEDS_REVIEW
    highest_threshold = -1.0
    for threshold in thresholds:
        minimum = threshold.min_percentage if hasattr(threshold, "min_percentage") else threshold["min_percentage"]
        band = threshold.band if hasattr(threshold, "band") else threshold["band"]
        band_enum = band if isinstance(band, MasteryBand) else MasteryBand(band)
        if overall_score >= minimum and minimum >= highest_threshold:
            winning_band = band_enum
            highest_threshold = minimum
    return winning_band


def _build_feedback(
    *,
    lowered: str,
    criterion_scores: list[CriterionScore],
    mastery_band: MasteryBand,
    rubric_criteria: list[RubricCriterion],
    expected_key_points: list[str],
) -> FeedbackResult:
    strengths: list[str] = []
    gaps: list[str] = []
    remediation_hints: list[str] = []

    criteria_by_name = {criterion.name: criterion for criterion in rubric_criteria}
    for criterion_score in criterion_scores:
        rubric_criterion = criteria_by_name[criterion_score.criterion_name]
        if criterion_score.score >= max(1, rubric_criterion.max_score - 1):
            strengths.append(f"You covered {criterion_score.criterion_name} well.")
        else:
            gaps.append(rubric_criterion.description)
            if rubric_criterion.failure_signals:
                remediation_hints.append(rubric_criterion.failure_signals[0])

    if "market cap" in lowered and "debt" not in lowered and "cash" not in lowered:
        gaps.append("Be careful not to treat market cap as a full substitute for enterprise value.")
        remediation_hints.append("If you mention market cap, also say what debt and cash do to the comparison.")

    if len(strengths) == 0 and expected_key_points:
        remediation_hints.append(f"Anchor the answer around this idea: {expected_key_points[0]}.")

    if mastery_band == MasteryBand.INTERVIEW_READY:
        next_step = "Move to a timed follow-up question and keep the same answer structure."
    elif mastery_band == MasteryBand.READY_FOR_RETRY:
        next_step = "Retry the answer out loud in 30 seconds and include one concrete metric."
    else:
        next_step = "Rewrite the answer using define, compare, apply before moving to the next concept."

    return FeedbackResult(
        strengths=strengths,
        gaps=gaps,
        next_step=next_step,
        remediation_hints=remediation_hints,
    )


def _build_multiple_choice_feedback(
    *,
    is_correct: bool,
    explanation: str,
    selected_option_id: str,
    correct_option_id: str | None,
) -> FeedbackResult:
    if is_correct:
        return FeedbackResult(
            strengths=["You selected the correct option."],
            gaps=[],
            next_step="Explain the logic behind that choice out loud before moving on.",
            remediation_hints=[explanation] if explanation else [],
        )

    hints = [explanation] if explanation else []
    gaps = ["The selected option does not match the strongest answer pattern for this concept."]
    if correct_option_id is not None:
        gaps.append(f"Review why `{correct_option_id}` is stronger than `{selected_option_id}`.")

    return FeedbackResult(
        strengths=[],
        gaps=gaps,
        next_step="Review the explanation, then retry the question without looking at the options first.",
        remediation_hints=hints,
    )


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    replacements = {
        "enterprise value": "ev",
        "equity value": "equityvalue",
        "market capitalization": "market cap",
        "p/e": "p / e",
        "ev/ebitda": "ev / ebitda",
    }
    for old, new in replacements.items():
        lowered = lowered.replace(old, new)
    return lowered


def _matches_fragment(lowered: str, fragment: str) -> bool:
    normalized_fragment = _normalize_text(fragment)
    if normalized_fragment in lowered:
        return True

    fragment_tokens = _meaningful_tokens(normalized_fragment)
    if not fragment_tokens:
        return False

    text_tokens = set(_meaningful_tokens(lowered))
    overlap = sum(1 for token in fragment_tokens if token in text_tokens)
    return overlap / len(fragment_tokens) >= 0.6


def _fragment_hits(lowered: str, fragments: list[str]) -> int:
    return sum(1 for fragment in fragments if _matches_fragment(lowered, fragment))


def _meaningful_tokens(text: str) -> list[str]:
    stopwords = {
        "the",
        "and",
        "is",
        "a",
        "an",
        "to",
        "of",
        "for",
        "in",
        "when",
        "it",
        "as",
        "what",
        "with",
        "be",
        "or",
        "by",
        "this",
        "that",
    }
    tokens = re.findall(r"[a-z0-9/+-]+", text.lower())
    return [token for token in tokens if token not in stopwords and len(token) > 1]
