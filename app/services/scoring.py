from __future__ import annotations

from fastapi import HTTPException

from app.core.enums import MasteryBand, ScoringMethod
from app.schemas.domain import CriterionScore, FeedbackResult, ScoreResult, StudentAttemptCreate
from app.seeds.reference_data import get_reference_module


REFERENCE_QUESTION_ID = "sample-question-enterprise-value"


def score_reference_attempt(attempt: StudentAttemptCreate) -> tuple[ScoreResult, FeedbackResult]:
    if attempt.question_id != REFERENCE_QUESTION_ID:
        raise HTTPException(status_code=404, detail="Unknown reference question.")

    if attempt.response.response_type != "free_text":
        raise HTTPException(status_code=400, detail="Reference scoring currently supports free_text only.")

    module = get_reference_module()
    content = attempt.response.content.strip()
    lowered = content.lower()

    criterion_scores = [
        _score_recall(lowered),
        _score_reasoning(lowered),
        _score_application(lowered),
        _score_clarity(content),
    ]
    overall_score = _calculate_overall_score(
        criterion_scores,
        module.question_bundle.rubric.criteria,
    )
    mastery_band = _resolve_mastery_band(overall_score, module.question_bundle.rubric.thresholds)
    feedback = _build_feedback(lowered, criterion_scores, mastery_band)

    score = ScoreResult(
        overall_score=overall_score,
        mastery_band=mastery_band,
        scoring_method=ScoringMethod.HYBRID,
        criterion_scores=criterion_scores,
    )
    return score, feedback


def _score_recall(lowered: str) -> CriterionScore:
    enterprise_signal = "enterprise value" in lowered or "ev " in f"{lowered} "
    equity_signal = "equity value" in lowered or "market cap" in lowered or "shareholder" in lowered
    if enterprise_signal and equity_signal:
        score = 4
        note = "Both enterprise value and equity value are explicitly distinguished."
    elif enterprise_signal or equity_signal:
        score = 2
        note = "One side of the definition is present, but the contrast is incomplete."
    else:
        score = 0
        note = "The answer does not establish the core definitions."
    return CriterionScore(criterion_name="recall", score=score, max_score=4, notes=note)


def _score_reasoning(lowered: str) -> CriterionScore:
    signals = [
        "capital structure",
        "debt",
        "cash",
        "leverage",
        "operating business",
        "normalize",
        "comparison",
    ]
    hits = sum(1 for signal in signals if signal in lowered)
    if hits >= 3:
        score = 4
        note = "The answer explains why EV-based comparisons work across financing structures."
    elif hits >= 2:
        score = 3
        note = "The core capital structure logic is present but still compressed."
    elif hits == 1:
        score = 1
        note = "There is a hint of reasoning, but not enough mechanism."
    else:
        score = 0
        note = "The answer asserts usefulness without explaining why."
    return CriterionScore(criterion_name="reasoning", score=score, max_score=4, notes=note)


def _score_application(lowered: str) -> CriterionScore:
    signals = [
        "ev / ebitda",
        "ev/ebitda",
        "multiple",
        "p / e",
        "p/e",
        "per-share",
        "interview",
        "compare companies",
    ]
    hits = sum(1 for signal in signals if signal in lowered)
    if hits >= 3:
        score = 4
        note = "The answer names concrete finance interview use cases and metrics."
    elif hits >= 2:
        score = 3
        note = "The answer is applied, but could use one more concrete metric or context."
    elif hits == 1:
        score = 1
        note = "There is one applied reference, but it still feels generic."
    else:
        score = 0
        note = "The answer never lands on a real use case."
    return CriterionScore(criterion_name="application", score=score, max_score=4, notes=note)


def _score_clarity(content: str) -> CriterionScore:
    word_count = len(content.split())
    has_structure = any(token in content for token in [".", ";", ":"])
    if word_count >= 35 and has_structure:
        score = 4
        note = "The answer is developed enough to sound deliberate under pressure."
    elif word_count >= 20:
        score = 3
        note = "The answer is concise and usable, but could be more structured."
    elif word_count >= 10:
        score = 2
        note = "The answer is brief and likely too compressed in a live interview."
    else:
        score = 0
        note = "The answer is too thin to be credible."
    return CriterionScore(criterion_name="clarity", score=score, max_score=4, notes=note)


def _calculate_overall_score(
    criterion_scores: list[CriterionScore],
    rubric_criteria: list,
) -> float:
    weighted_total = 0.0
    for criterion_score, rubric_criterion in zip(criterion_scores, rubric_criteria, strict=True):
        weighted_total += (criterion_score.score / criterion_score.max_score) * rubric_criterion.weight
    return round(weighted_total * 100, 1)


def _resolve_mastery_band(overall_score: float, thresholds: list) -> MasteryBand:
    winning_band = MasteryBand.NEEDS_REVIEW
    highest_threshold = -1.0
    for threshold in thresholds:
        if overall_score >= threshold.min_percentage and threshold.min_percentage >= highest_threshold:
            winning_band = threshold.band
            highest_threshold = threshold.min_percentage
    return winning_band


def _build_feedback(
    lowered: str,
    criterion_scores: list[CriterionScore],
    mastery_band: MasteryBand,
) -> FeedbackResult:
    strengths: list[str] = []
    gaps: list[str] = []
    remediation_hints: list[str] = []

    score_map = {criterion.criterion_name: criterion.score for criterion in criterion_scores}
    if score_map["recall"] >= 3:
        strengths.append("You distinguished enterprise value from equity value instead of collapsing them together.")
    else:
        gaps.append("Define both enterprise value and equity value before moving into comparisons.")
        remediation_hints.append("Start with the two definitions, then explain what each one measures.")

    if score_map["reasoning"] >= 3:
        strengths.append("You explained the capital structure logic instead of just naming the metric.")
    else:
        gaps.append("Explain why debt, cash, or leverage differences make EV-based comparisons more useful.")
        remediation_hints.append("Say explicitly that EV normalizes financing differences across companies.")

    if score_map["application"] >= 3:
        strengths.append("You connected the answer to a real valuation or interview use case.")
    else:
        gaps.append("Name a concrete multiple like EV / EBITDA and contrast it with a per-share metric like P / E.")
        remediation_hints.append("End the answer with one EV-based multiple and one case where equity value still matters.")

    if score_map["clarity"] < 3:
        gaps.append("The answer is still too compressed to sound confident in a live interview.")
        remediation_hints.append("Use a three-part structure: define, compare, apply.")

    if "market cap" in lowered and "debt" not in lowered and "cash" not in lowered:
        gaps.append("Be careful not to treat market cap as a full substitute for enterprise value.")
        remediation_hints.append("If you mention market cap, also say what debt and cash do to the comparison.")

    if mastery_band == MasteryBand.INTERVIEW_READY:
        next_step = "Move to a timed follow-up question and keep the same answer structure."
    elif mastery_band == MasteryBand.READY_FOR_RETRY:
        next_step = "Retry the answer out loud in 30 seconds and include one EV-based multiple."
    else:
        next_step = "Rewrite the answer using define, compare, apply before moving to the next concept."

    return FeedbackResult(
        strengths=strengths,
        gaps=gaps,
        next_step=next_step,
        remediation_hints=remediation_hints,
    )

