// @vitest-environment jsdom
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Route, MemoryRouter, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  AuthoredQuestionBundleRecord,
  ContentStatusTransitionResult,
  PracticeSessionRecord,
} from "../../types/api";

const { navigateSpy, getAuthoredQuestionMock, transitionAuthoredQuestionStatusMock, createPracticeSessionMock } =
  vi.hoisted(() => ({
    navigateSpy: vi.fn(),
    getAuthoredQuestionMock: vi.fn(),
    transitionAuthoredQuestionStatusMock: vi.fn(),
    createPracticeSessionMock: vi.fn(),
  }));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");

  return {
    ...actual,
    useNavigate: () => navigateSpy,
  };
});

vi.mock("../../api/authored", () => ({
  getAuthoredQuestion: getAuthoredQuestionMock,
  transitionAuthoredQuestionStatus: transitionAuthoredQuestionStatusMock,
}));

vi.mock("../../api/practiceSessions", () => ({
  createPracticeSession: createPracticeSessionMock,
}));

import { ReviewPublishPage } from "../ReviewPublishPage";

function makeBundle(status: AuthoredQuestionBundleRecord["question"]["status"]): AuthoredQuestionBundleRecord {
  const reviewNotes = status === "draft" ? null : "Operator verified the rubric and answer.";

  return {
    topic: {
      id: "topic-1",
      slug: "valuation",
      title: "Valuation",
      description: "Interview practice for valuation basics.",
      order_index: 1,
      status: "draft",
    },
    concept: {
      id: "concept-1",
      topic_slug: "valuation",
      slug: "enterprise-value",
      title: "Enterprise Value",
      definition: "How to bridge enterprise value and equity value.",
      difficulty: "intermediate",
      prerequisites: ["net-debt-basics"],
      status: "draft",
    },
    assessment_mode: {
      mode: "short_answer",
      description: "Interview-style free response.",
      scoring_style: "rubric",
      timing_style: "untimed",
    },
    question: {
      id: "question-123",
      concept_slug: "enterprise-value",
      external_id: null,
      assessment_mode: "short_answer",
      difficulty: "intermediate",
      author_type: "human",
      status,
      prompt: "Explain enterprise value versus equity value.",
      context: "Use a concise interview answer.",
      payload: {
        question_type: "short_answer",
        prompt: "Explain enterprise value versus equity value.",
        context: "Use a concise interview answer.",
        max_duration_seconds: 90,
        response_guidance: ["Define both terms.", "Explain the bridge.", "Tie it back to interview use."],
      },
      version: 1,
    },
    rubric: {
      scoring_style: "rubric",
      criteria: [
        {
          name: "Definition clarity",
          description: "Distinguishes the two concepts clearly.",
          weight: 1,
          min_score: 0,
          max_score: 2,
          failure_signals: ["Confuses EV with equity value"],
          strong_response_fragments: ["enterprise value", "equity value"],
        },
        {
          name: "Bridge mechanics",
          description: "Explains the standard adjustments.",
          weight: 1,
          min_score: 0,
          max_score: 2,
          failure_signals: ["Omits debt or cash"],
          strong_response_fragments: ["net debt", "cash"],
        },
      ],
      thresholds: [
        { band: "needs_review", min_percentage: 0 },
        { band: "partial", min_percentage: 55 },
        { band: "ready_for_retry", min_percentage: 75 },
      ],
      review_notes: reviewNotes,
    },
    expected_answer: {
      answer_text: "Enterprise value describes the operating business; equity value describes the shareholders' stake.",
      answer_outline: ["Define EV.", "Define equity value.", "Explain the bridge."],
      key_points: ["EV is operating value.", "Equity value is the ownership claim."],
      acceptable_variants: ["EV is the whole business, equity value is the stock value."],
    },
    common_mistakes: [
      {
        mistake_text: "Treating EV and market cap as identical.",
        why_it_is_wrong: "It skips debt and cash adjustments.",
        remediation_hint: "State the bridge explicitly.",
      },
    ],
  };
}

function makeSession(): PracticeSessionRecord {
  return {
    session_id: "session-456",
    user_id: "operator-1",
    source: "demo",
    status: "created",
    question_queue: ["question-123"],
    queued_question_count: 1,
    completed_question_count: 0,
    remaining_question_count: 1,
    current_question_id: null,
    started_at: "2026-04-11T08:00:00Z",
    completed_at: null,
    attempts: [],
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/operator/questions/question-123/review"]}>
      <Routes>
        <Route path="/operator/questions/:questionId/review" element={<ReviewPublishPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ReviewPublishPage", () => {
  beforeEach(() => {
    navigateSpy.mockReset();
    getAuthoredQuestionMock.mockReset();
    transitionAuthoredQuestionStatusMock.mockReset();
    createPracticeSessionMock.mockReset();
  });

  it("moves a draft question through review and publish, then creates a demo session", async () => {
    const reviewedNotes = "Looks sharp and ready for the demo.";
    const draftBundle = makeBundle("draft");
    const reviewedBundle = makeBundle("reviewed");
    reviewedBundle.rubric.review_notes = reviewedNotes;
    const publishedBundle = makeBundle("published");
    publishedBundle.rubric.review_notes = reviewedNotes;

    getAuthoredQuestionMock
      .mockResolvedValueOnce(draftBundle)
      .mockResolvedValueOnce(reviewedBundle)
      .mockResolvedValueOnce(publishedBundle);
    transitionAuthoredQuestionStatusMock
      .mockResolvedValueOnce({
        question_id: "question-123",
        previous_status: "draft",
        current_status: "reviewed",
        review_notes: reviewedNotes,
      } satisfies ContentStatusTransitionResult)
      .mockResolvedValueOnce({
        question_id: "question-123",
        previous_status: "reviewed",
        current_status: "published",
        review_notes: reviewedNotes,
      } satisfies ContentStatusTransitionResult);
    createPracticeSessionMock.mockResolvedValue(makeSession());

    renderPage();

    await screen.findByRole("button", { name: /mark reviewed/i });

    fireEvent.change(screen.getByPlaceholderText("Add the operator quality note here."), {
      target: { value: reviewedNotes },
    });
    fireEvent.click(screen.getByRole("button", { name: /mark reviewed/i }));

    await waitFor(() => {
      expect(transitionAuthoredQuestionStatusMock).toHaveBeenCalledWith("question-123", {
        status: "reviewed",
        review_notes: reviewedNotes,
      });
    });

    await screen.findByRole("button", { name: /publish question/i });
    fireEvent.click(screen.getByRole("button", { name: /publish question/i }));

    await waitFor(() => {
      expect(transitionAuthoredQuestionStatusMock).toHaveBeenCalledWith("question-123", {
        status: "published",
        review_notes: reviewedNotes,
      });
    });

    const createSessionButton = await screen.findByRole("button", { name: /create demo session/i });
    fireEvent.click(createSessionButton);

    await waitFor(() => {
      expect(createPracticeSessionMock).toHaveBeenCalledWith({
        source: "demo",
        question_queue: ["question-123"],
      });
    });

    expect(navigateSpy).toHaveBeenCalledWith("/operator/sessions/session-456");
  });
});
