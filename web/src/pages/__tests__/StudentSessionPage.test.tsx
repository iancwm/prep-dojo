// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { Route, Routes, MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as authoredApi from "../../api/authored";
import * as practiceSessionsApi from "../../api/practiceSessions";
import ResultPage from "../ResultPage";
import StudentSessionPage from "../StudentSessionPage";
import {
  completedSession,
  createdSession,
  startedSession,
  studentBundle,
  studentQuestionId,
  studentResponseText,
  studentSessionId,
  submitResult,
} from "./studentFixtures";

describe("StudentSessionPage smoke flow", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  it("starts a session, submits an answer, and opens the scored result", async () => {
    vi.spyOn(practiceSessionsApi, "getPracticeSession")
      .mockResolvedValueOnce(createdSession)
      .mockResolvedValueOnce(completedSession);
    vi.spyOn(practiceSessionsApi, "startPracticeSession").mockResolvedValue(startedSession);
    vi.spyOn(authoredApi, "getAuthoredQuestion").mockResolvedValue(studentBundle);
    vi.spyOn(authoredApi, "submitAuthoredQuestionAttempt").mockResolvedValue(submitResult);

    render(
      <MemoryRouter initialEntries={[`/practice/${studentSessionId}`]}>
        <Routes>
          <Route path="/practice/:sessionId" element={<StudentSessionPage />} />
          <Route path="/practice/:sessionId/result" element={<ResultPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("button", { name: /start practice/i })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: /start practice/i }));

    const answerField = await screen.findByLabelText(/response/i);
    fireEvent.change(answerField, { target: { value: studentResponseText } });
    fireEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    expect(await screen.findByRole("button", { name: /view result/i })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: /view result/i }));

    expect(await screen.findByRole("heading", { name: /interview ready/i })).toBeInTheDocument();
    expect(screen.getByText(/how the answer was read/i)).toBeInTheDocument();
    expect(screen.getByText(/what stands out/i)).toBeInTheDocument();
    expect(screen.getByText(/use the result to keep the loop moving/i)).toBeInTheDocument();

    expect(practiceSessionsApi.getPracticeSession).toHaveBeenCalledTimes(2);
    expect(practiceSessionsApi.startPracticeSession).toHaveBeenCalledWith(studentSessionId);
    expect(authoredApi.getAuthoredQuestion).toHaveBeenCalledWith(studentQuestionId);
    expect(authoredApi.submitAuthoredQuestionAttempt).toHaveBeenCalledWith(
      studentQuestionId,
      expect.objectContaining({
        question_id: studentQuestionId,
        session_id: studentSessionId,
        status: "submitted",
        response: expect.objectContaining({
          response_type: "free_text",
          content: studentResponseText,
        }),
      }),
    );
  });
});
